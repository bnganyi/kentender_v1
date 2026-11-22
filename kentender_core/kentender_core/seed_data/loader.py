
import json
from pathlib import Path
from collections import defaultdict

import frappe
from frappe.utils import now_datetime
from frappe.utils.password import update_password

from kentender_core.services import responsibility_administration
from kentender_core.services.organisation_structure import (
    structure_conflicts,
    require_whole_structure,
)


SEED_NAME = "eprocurement_selected_users"
MARKER_DOCTYPE = "System Settings"
MARKER_FIELD = "kentender_eprocurement_users_seed_installed"
ASSIGNMENT_ACTOR = "Administrator"


# =========================================================
# SEED FILE
# =========================================================

def _seed_path():
    return (
        Path(frappe.get_app_path("kentender_core"))
        / "seed_data"
        / "eprocurement_users.json"
    )


def _load_seed():
    path = _seed_path()

    if not path.exists():
        raise FileNotFoundError(
            f"Seed file not found: {path}"
        )

    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


# =========================================================
# INSTALLATION MARKER
# =========================================================

def _installation_marker():
    result = frappe.db.sql(
        """
        SELECT value
        FROM `tabSingles`
        WHERE doctype = %s
          AND field = %s
        LIMIT 1
        """,
        (MARKER_DOCTYPE, MARKER_FIELD),
    )

    return result[0][0] if result else None


def _set_installation_marker():
    frappe.db.sql(
        """
        INSERT INTO `tabSingles`
            (doctype, field, value)
        VALUES
            (%s, %s, %s)
        ON DUPLICATE KEY UPDATE
            value = VALUES(value)
        """,
        (
            MARKER_DOCTYPE,
            MARKER_FIELD,
            now_datetime().isoformat(),
        ),
    )


# =========================================================
# ORGANISATION ROOT MAPPING
# =========================================================

def _organisation_unit_mapping(seed):
    """
    Map the source root PE-MOH to the existing destination
    root CODE1.

    The destination root is reused and never duplicated.
    """

    source_roots = [
        row
        for row in seed["organisation_units"]
        if not row.get("parent_organisation_unit")
    ]

    destination_roots = frappe.get_all(
        "Organisation Unit",
        filters={
            "parent_organisation_unit": ("is", "not set")
        },
        fields=[
            "name",
            "unit_name",
            "status",
        ],
        limit_page_length=0,
    )

    if len(source_roots) != 1:
        raise ValueError(
            "Expected exactly one source root; "
            f"found {len(source_roots)}."
        )

    if len(destination_roots) != 1:
        raise ValueError(
            "Expected exactly one destination root; "
            f"found {len(destination_roots)}."
        )

    source_root = source_roots[0]
    destination_root = destination_roots[0]

    source_name = (
        source_root.get("unit_name") or ""
    ).strip().casefold()

    destination_name = (
        destination_root.unit_name or ""
    ).strip().casefold()

    if source_name != destination_name:
        raise ValueError(
            "Source and destination root names do not match: "
            f"{source_root.get('unit_name')} / "
            f"{destination_root.unit_name}"
        )

    if destination_root.status != "Active":
        raise ValueError(
            "Destination root is not Active."
        )

    return {
        source_root["name"]: destination_root.name
    }


# =========================================================
# SEED STRUCTURAL VALIDATION
# =========================================================

def _validate_seed_structure(seed):
    errors = []
    warnings = []

    required_keys = [
        "manifest",
        "organisation_units",
        "responsibility_assignments",
        "users",
        "role_profiles",
        "role_permissions",
        "user_permissions",
        "document_shares",
        "roles",
        "default_password",
    ]

    for key in required_keys:
        if key not in seed:
            errors.append(
                f"Missing seed section: {key}"
            )

    if errors:
        return errors, warnings

    manifest = seed["manifest"]

    if manifest.get("seed_name") != SEED_NAME:
        errors.append("Unexpected seed name.")

    if not seed.get("default_password"):
        errors.append("Default password is missing.")

    if not manifest.get("passwords_included"):
        errors.append(
            "Manifest does not confirm password inclusion."
        )

    users = seed["users"]
    roles = seed["roles"]
    units = seed["organisation_units"]
    assignments = seed["responsibility_assignments"]
    permissions = seed["role_permissions"]

    user_emails = [
        row["email"] for row in users
    ]

    if len(user_emails) != len(set(user_emails)):
        errors.append(
            "Duplicate user email addresses."
        )

    unit_names = {
        row["name"] for row in units
    }

    if len(unit_names) != len(units):
        errors.append(
            "Duplicate Organisation Unit names."
        )

    role_names = {
        row["name"] for row in roles
    }

    if len(role_names) != len(roles):
        errors.append(
            "Duplicate roles in seed."
        )

    # Validate user role references.
    for user in users:
        if not user.get("email"):
            errors.append(
                "A user has no email address."
            )

        for role_row in user.get("roles", []):
            if role_row.get("role") not in role_names:
                errors.append(
                    f"User {user.get('email')} references "
                    f"an unexported role: {role_row.get('role')}"
                )

    # Validate responsibility references.
    for assignment in assignments:
        if assignment.get("user") not in user_emails:
            errors.append(
                "Assignment references an unexported user: "
                f"{assignment.get('user')}"
            )

        unit = assignment.get("organisation_unit")

        if unit and unit not in unit_names:
            errors.append(
                "Assignment references an unexported "
                f"Organisation Unit: {unit}"
            )

    # Validate permissions.
    # Multiple records with the same parent, role and
    # permlevel are allowed and must be preserved.
    for permission in permissions:
        if permission.get("role") not in role_names:
            errors.append(
                "Permission references an unexported role: "
                f"{permission.get('role')}"
            )

        if not permission.get("parent"):
            errors.append(
                "Permission record has no parent DocType."
            )

        if permission.get("permlevel") is None:
            errors.append(
                "Permission record has no permission level: "
                f"{permission.get('parent')} / "
                f"{permission.get('role')}"
            )

    if seed.get("user_permissions"):
        warnings.append(
            "User Permissions are present but are not imported."
        )

    if seed.get("role_profiles"):
        warnings.append(
            "Role Profiles are present but are not imported."
        )

    if seed.get("document_shares"):
        warnings.append(
            "Document Shares are skipped because the exported "
            "records are self-shares."
        )

    return errors, warnings


# =========================================================
# DESTINATION VALIDATION
# =========================================================

def _validate_destination(seed):
    errors = []
    warnings = []

    if frappe.session.user != "Administrator":
        errors.append(
            "Run the import as Administrator."
        )

    if "System Manager" not in frappe.get_roles(
        "Administrator"
    ):
        errors.append(
            "Administrator does not have System Manager."
        )

    if _installation_marker():
        errors.append(
            "This seed has already been installed on this site."
        )

    # Validate root mapping.
    try:
        mapping = _organisation_unit_mapping(seed)

        destination_root = next(
            iter(mapping.values())
        )

        existing_units = frappe.get_all(
            "Organisation Unit",
            pluck="name",
            limit_page_length=0,
        )

        unexpected = [
            name
            for name in existing_units
            if name != destination_root
        ]

        if unexpected:
            errors.append(
                "Unexpected existing Organisation Units: "
                + ", ".join(unexpected)
            )
        else:
            source_root = next(iter(mapping))

            warnings.append(
                f"Source root {source_root} will reuse "
                f"destination root {destination_root}."
            )

    except Exception as exc:
        errors.append(
            f"Organisation root mapping failed: {exc}"
        )

    # Validate installed applications.
    installed_apps = set(
        frappe.get_installed_apps()
    )

    source_apps = set(
        seed["manifest"].get("source_apps", [])
    )

    missing_apps = source_apps - installed_apps

    if missing_apps:
        errors.append(
            "Missing destination applications: "
            + ", ".join(sorted(missing_apps))
        )

    # Validate roles.
    for role in seed["roles"]:
        if not frappe.db.exists(
            "Role", role["name"]
        ):
            errors.append(
                f"Missing destination role: {role['name']}"
            )

    # Validate permission DocTypes.
    doctypes = {
        row["parent"]
        for row in seed["role_permissions"]
    }

    for doctype in sorted(doctypes):
        if not frappe.db.exists(
            "DocType", doctype
        ):
            errors.append(
                f"Missing permission DocType: {doctype}"
            )

    # Validate registered business roles.
    for assignment in seed["responsibility_assignments"]:
        try:
            responsibility_administration.require_registered(
                assignment["business_role"]
            )
        except Exception as exc:
            errors.append(
                f"Invalid business role "
                f"{assignment['business_role']}: {exc}"
            )

    # Validate organisation structure.
    conflicts = structure_conflicts()

    if conflicts:
        errors.extend(conflicts)

    try:
        require_whole_structure()
    except Exception as exc:
        errors.append(
            f"Organisation structure validation failed: {exc}"
        )

    # Existing users are allowed.
    # Their passwords will not be changed.
    for user in seed["users"]:
        email = user["email"]

        if frappe.db.exists("User", email):
            warnings.append(
                "Existing user will be updated without changing "
                f"their password: {email}"
            )

    return errors, warnings


# =========================================================
# VALIDATION ENTRY POINT
# =========================================================

def validate_eprocurement_seed():
    print(
        "\n========== KENTENDER SEED VALIDATION =========="
    )

    seed = _load_seed()

    structural_errors, structural_warnings = (
        _validate_seed_structure(seed)
    )

    destination_errors, destination_warnings = (
        _validate_destination(seed)
    )

    errors = (
        structural_errors + destination_errors
    )

    warnings = (
        structural_warnings + destination_warnings
    )

    print("Site:", frappe.local.site)
    print(
        "Seed:",
        seed["manifest"].get("seed_name")
    )
    print(
        "Source:",
        seed["manifest"].get("source_site")
    )

    print("\n========== RECORD COUNTS ==========")

    for key in [
        "users",
        "roles",
        "organisation_units",
        "responsibility_assignments",
        "role_permissions",
        "user_permissions",
        "role_profiles",
        "document_shares",
    ]:
        print(
            f"{key}: {len(seed.get(key, []))}"
        )

    print("\n========== WARNINGS ==========")

    for warning in warnings:
        print("WARNING:", warning)

    print("\n========== ERRORS ==========")

    for error in errors:
        print("ERROR:", error)

    if errors:
        print(
            "\nVALIDATION FAILED. No data was changed."
        )

        return {
            "valid": False,
            "errors": errors,
            "warnings": warnings,
        }

    print(
        "\nVALIDATION PASSED. No data was changed."
    )

    return {
        "valid": True,
        "errors": [],
        "warnings": warnings,
    }


# =========================================================
# ORGANISATION UNIT IMPORT
# =========================================================

def _create_organisation_units(seed):
    """
    Reuse the existing destination root and create
    the remaining units in parent-first order.
    """

    mapping = _organisation_unit_mapping(seed)

    pending = {
        row["name"]: row
        for row in seed["organisation_units"]
        if row["name"] not in mapping
    }

    created = []

    while pending:
        progress = False

        for name, row in list(pending.items()):
            source_parent = row.get(
                "parent_organisation_unit"
            )

            destination_parent = mapping.get(
                source_parent,
                source_parent,
            )

            if destination_parent and not frappe.db.exists(
                "Organisation Unit",
                destination_parent,
            ):
                continue

            fields = [
                "unit_code",
                "org_unit_reference",
                "unit_name",
                "status",
                "hrms_department",
                "fixture_namespace",
                "procuring_entity",
                "unit_type",
                "effective_from",
                "effective_to",
            ]

            values = {
                field: row.get(field)
                for field in fields
            }

            values["parent_organisation_unit"] = (
                destination_parent or None
            )

            old_parent = row.get("old_parent")

            values["old_parent"] = mapping.get(
                old_parent,
                old_parent,
            )

            doc = frappe.get_doc({
                "doctype": "Organisation Unit",
                **values,
            })

            doc.insert(ignore_permissions=True)

            mapping[name] = doc.name
            created.append(doc.name)

            del pending[name]
            progress = True

        if not progress:
            raise Exception(
                "Cannot resolve Organisation Unit hierarchy: "
                + ", ".join(pending.keys())
            )

    require_whole_structure()

    return {
        "created": created,
        "mapping": mapping,
    }


# =========================================================
# USER IMPORT
# =========================================================

def _create_users(seed):
    created = []
    updated = []

    password = seed["default_password"]

    for row in seed["users"]:
        email = row["email"]

        if frappe.db.exists("User", email):
            doc = frappe.get_doc(
                "User", email
            )

            # Update selected profile fields.
            for field in [
                "first_name",
                "middle_name",
                "last_name",
                "language",
                "time_zone",
                "enabled",
                "user_type",
            ]:
                if field in row:
                    doc.set(field, row[field])

            existing_roles = {
                role.role for role in doc.roles
            }

            # Add missing selected roles.
            # Preserve unrelated destination roles.
            for role_row in row.get("roles", []):
                role_name = role_row["role"]

                if role_name not in existing_roles:
                    doc.append(
                        "roles",
                        {"role": role_name},
                    )

            doc.save(ignore_permissions=True)
            updated.append(email)

        else:
            doc = frappe.get_doc({
                "doctype": "User",
                "email": email,
                "first_name": row.get("first_name"),
                "middle_name": row.get("middle_name"),
                "last_name": row.get("last_name"),
                "language": row.get("language") or "en",
                "time_zone": row.get("time_zone"),
                "enabled": row.get("enabled", 1),
                "user_type": (
                    row.get("user_type") or "System User"
                ),
                "roles": [
                    {"role": role_row["role"]}
                    for role_row in row.get("roles", [])
                ],
            })

            doc.flags.no_welcome_mail = True
            doc.insert(ignore_permissions=True)

            update_password(
                email,
                password,
            )

            created.append(email)

    return {
        "created": created,
        "updated": updated,
    }


# =========================================================
# ROLE PERMISSION IMPORT
# =========================================================

def _import_role_permissions(seed):
    """
    Import DocType permissions directly into tabDocPerm.

    This avoids saving standard DocType definitions, which
    requires Developer Mode.

    Existing permissions for unrelated roles are preserved.

    Every source permission record is inserted, including
    repeated role/permission-level combinations.
    """

    grouped = defaultdict(list)

    selected_roles = {
        row["name"]
        for row in seed["roles"]
    }

    for row in seed["role_permissions"]:
        grouped[row["parent"]].append(row)

    permission_fields = [
        "match",
        "permlevel",
        "read",
        "write",
        "create",
        "submit",
        "cancel",
        "delete",
        "amend",
        "report",
        "export",
        "import",
        "share",
        "print",
        "email",
        "if_owner",
        "select",
        "mask",
        "impersonate",
    ]

    defaults = {
        "read": 1,
        "write": 1,
        "create": 1,
        "submit": 0,
        "cancel": 0,
        "delete": 1,
        "amend": 0,
        "report": 1,
        "export": 1,
        "import": 0,
        "share": 1,
        "print": 1,
        "email": 1,
        "if_owner": 0,
        "select": 0,
        "mask": 0,
        "impersonate": 0,
    }

    inserted_count = 0
    deleted_count = 0
    updated_doctypes = []

    for doctype, rows in grouped.items():

        # Count existing selected-role records first.
        placeholders = ", ".join(
            ["%s"] * len(selected_roles)
        )

        filter_values = (
            [doctype] + sorted(selected_roles)
        )

        existing_count = frappe.db.sql(
            f"""
            SELECT COUNT(*)
            FROM `tabDocPerm`
            WHERE parent = %s
              AND parenttype = 'DocType'
              AND parentfield = 'permissions'
              AND role IN ({placeholders})
            """,
            tuple(filter_values),
        )[0][0]

        # Delete only selected-role permissions.
        frappe.db.sql(
            f"""
            DELETE FROM `tabDocPerm`
            WHERE parent = %s
              AND parenttype = 'DocType'
              AND parentfield = 'permissions'
              AND role IN ({placeholders})
            """,
            tuple(filter_values),
        )

        deleted_count += existing_count

        # Find the last remaining child row index.
        current_idx = frappe.db.sql(
            """
            SELECT COALESCE(MAX(idx), 0)
            FROM `tabDocPerm`
            WHERE parent = %s
              AND parenttype = 'DocType'
              AND parentfield = 'permissions'
            """,
            (doctype,),
        )[0][0]

        # Preserve source row order.
        rows = sorted(
            rows,
            key=lambda row: row.get("idx") or 0,
        )

        for row in rows:
            current_idx += 1
            now = now_datetime()

            values = {
                "name": frappe.generate_hash(length=20),
                "creation": now,
                "modified": now,
                "modified_by": ASSIGNMENT_ACTOR,
                "owner": ASSIGNMENT_ACTOR,
                "docstatus": 0,
                "parent": doctype,
                "parentfield": "permissions",
                "parenttype": "DocType",
                "idx": current_idx,
                "role": row["role"],
            }

            for field in permission_fields:
                values[field] = row.get(field)

            # Apply Frappe defaults for omitted permission flags.
            for field, default in defaults.items():
                if values[field] is None:
                    values[field] = default

            columns = list(values.keys())

            column_sql = ", ".join(
                f"`{column}`" for column in columns
            )

            value_placeholders = ", ".join(
                ["%s"] * len(columns)
            )

            insert_query = f"""
                INSERT INTO `tabDocPerm`
                    ({column_sql})
                VALUES
                    ({value_placeholders})
            """

            frappe.db.sql(
                insert_query,
                tuple(
                    values[column]
                    for column in columns
                ),
            )

            inserted_count += 1

        updated_doctypes.append(doctype)

        # Clear the affected DocType cache.
        frappe.clear_cache(doctype=doctype)

    print(
        f"DocPerm records deleted: {deleted_count}"
    )

    print(
        f"DocPerm records inserted: {inserted_count}"
    )

    return updated_doctypes


# =========================================================
# BUSINESS RESPONSIBILITY IMPORT
# =========================================================

def _create_responsibility_assignments(
    seed,
    organisation_mapping,
):
    created = []
    existing = []

    for row in seed["responsibility_assignments"]:
        source_unit = row.get(
            "organisation_unit"
        )

        destination_unit = organisation_mapping.get(
            source_unit,
            source_unit,
        )

        result = responsibility_administration.grant(
            user=row["user"],
            business_role=row["business_role"],
            organisation_unit=destination_unit or "",
            appointment_type=(
                row.get("appointment_type") or "Permanent"
            ),
            authority_reference=(
                row.get("authority_reference") or ""
            ),
            effective_from=row.get("effective_from"),
            effective_to=row.get("effective_to"),
            fixture_namespace=(
                row.get("fixture_namespace") or ""
            ),
            actor=ASSIGNMENT_ACTOR,
            scope_reference=(
                row.get("scope_reference") or ""
            ),
        )

        if result.get("created"):
            created.append(
                result["assignment"]
            )
        else:
            existing.append(
                result["assignment"]
            )

    return {
        "created": created,
        "existing": existing,
    }


# =========================================================
# MAIN IMPORT ENTRY POINT
# =========================================================

def import_eprocurement_seed():
    print(
        "\n========== KENTENDER SEED IMPORT =========="
    )

    validation = validate_eprocurement_seed()

    if not validation["valid"]:
        raise Exception(
            "Seed validation failed. "
            "Resolve all errors before importing."
        )

    seed = _load_seed()

    print("\nStarting seed installation...")

    try:
        # 1. Organisation Units.
        organisation_result = (
            _create_organisation_units(seed)
        )

        print(
            "Organisation Units created:",
            len(organisation_result["created"]),
        )

        print(
            "Organisation root mapping:",
            organisation_result["mapping"],
        )

        # 2. Users and Frappe roles.
        user_result = _create_users(seed)

        print(
            "Users created:",
            len(user_result["created"]),
        )

        print(
            "Existing users updated:",
            len(user_result["updated"]),
        )

        # 3. DocType permissions.
        updated_doctypes = (
            _import_role_permissions(seed)
        )

        print(
            "DocTypes updated:",
            len(updated_doctypes),
        )

        # 4. Business responsibilities.
        assignment_result = (
            _create_responsibility_assignments(
                seed,
                organisation_result["mapping"],
            )
        )

        print(
            "Responsibilities created:",
            len(assignment_result["created"]),
        )

        print(
            "Existing responsibilities:",
            len(assignment_result["existing"]),
        )

        # 5. Installation marker.
        _set_installation_marker()

        # Commit after all import operations succeed.
        frappe.db.commit()

        report = {
            "site": frappe.local.site,
            "seed": SEED_NAME,
            "organisation_units_created": len(
                organisation_result["created"]
            ),
            "organisation_root_mapping": (
                organisation_result["mapping"]
            ),
            "users_created": len(
                user_result["created"]
            ),
            "users_updated": len(
                user_result["updated"]
            ),
            "doctypes_updated": len(
                updated_doctypes
            ),
            "responsibilities_created": len(
                assignment_result["created"]
            ),
            "responsibilities_existing": len(
                assignment_result["existing"]
            ),
            "document_shares_skipped": len(
                seed.get("document_shares", [])
            ),
            "user_permissions_skipped": len(
                seed.get("user_permissions", [])
            ),
            "role_profiles_skipped": len(
                seed.get("role_profiles", [])
            ),
        }

        print(
            "\n========== IMPORT SUCCESSFUL =========="
        )

        print(
            json.dumps(
                report,
                indent=4,
                default=str,
            )
        )

        return report

    except Exception:
        frappe.db.rollback()

        print(
            "\nIMPORT FAILED. Database rollback requested."
        )

        raise

