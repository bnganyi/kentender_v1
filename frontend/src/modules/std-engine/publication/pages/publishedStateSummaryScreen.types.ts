export type PublishedStateSummaryScreenProps = {
	tenderCode: string;
	/** Business snapshot identifier (display). */
	snapshotCode: string;
	bundleVersion: string;
	dsmVersion: string;
	domVersion: string;
	demVersion: string;
	dcmVersion: string;
	evidencePackageHref: string;
	evidencePackageLinkLabel?: string;
	nextLifecycleStep: string;
	/** Host-supplied addendum / reissue copy (pack: guidance shown). */
	addendumReissueGuidance: string;
};
