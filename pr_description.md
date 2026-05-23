🎯 **What:** The vulnerability fixed
Fixed an Unrestricted File Upload vulnerability in the `/api/analyze` endpoint.

⚠️ **Risk:** The potential impact if left unfixed
By not checking the uploaded file extension, an attacker could upload malicious scripts (e.g., `.php`, `.sh`, `.py`, `.exe`). If the `uploads` directory were accessible or the files were processed unsafely by other parts of the system, this could lead to Stored Cross-Site Scripting (XSS) or Remote Code Execution (RCE).

🛡️ **Solution:** How the fix addresses the vulnerability
Added an `ALLOWED_EXTENSIONS` set (`png`, `jpg`, `jpeg`, `gif`, `webp`) and an `allowed_file` helper function to safely validate the file extension. The `/api/analyze` route now rejects any files that do not have an approved image extension with a 400 Bad Request response. Unit tests were added to verify the validation logic.
