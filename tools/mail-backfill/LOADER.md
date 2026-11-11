# Database loader — instructions

You are loading prepared records into a company database. Mechanical job: copy, do not edit.

Tool: `ArtifactData` (load it with ToolSearch `select:ArtifactData` if it is not already
available). If it is not available at all, reply `unavailable` and stop.

Artifact URL for every call: `https://claude.ai/artifact/BzDjpcTEGnMWXwPZfpLxG4`

Your task lists batch files. Each batch file is a JSON list of up to 50 write entries of the form
`{"op": "set", "collection": "...", "doc_id": "...", "file_path": "..."}`.

For each batch file, in order:
1. Read the batch file with the Read tool.
2. Call `ArtifactData` with `action: "batch"`, the `url` above, and `writes` set to the list
   exactly as it is in the file — every entry, every field, character for character. Do not open
   the documents the `file_path`s point to; the tool reads them itself. Do not add `if_version`.
3. If the call succeeds, go to the next file. If it fails, read the error: fix only an obvious
   copying mistake on your side and retry that batch once. If it fails again, record the batch
   file name and the error text, and carry on with the next file.

Do not write anything else, do not delete anything, do not touch any other collection or
artifact, do not spawn agents.

Final reply, one line: `loaded <n> batches, failed: <file names with a few words of the error, or none>`
