document.addEventListener("DOMContentLoaded", function() {
    const form = document.getElementById("registerForm");
    const password = document.getElementById("password");
    const confirmPassword = document.getElementById("confirm_password");
    const passwordError = document.getElementById("passwordError");

    form.addEventListener("submit", function(event) {
        if (password.value !== confirmPassword.value) {
            event.preventDefault(); // Stop form submission
            passwordError.style.display = "block"; // Show error message
            confirmPassword.style.border = "2px solid red"; // Highlight field in red
        } else {
            passwordError.style.display = "none"; // Hide error if valid
            confirmPassword.style.border = "1px solid #ccc"; // Reset border
        }
    });
});