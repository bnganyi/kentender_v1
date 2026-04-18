# Frappe Create Artifact

1. Determine whether the requested artifact is framework-managed.
2. If yes, do not write scaffold files manually.
3. Output:
   - the exact Bench/Frappe command to run
   - the expected generated location
   - the files that will be modified afterward
4. Stop and wait unless explicitly told to continue after generation.
5. After scaffold generation exists, modify only the required generated files.