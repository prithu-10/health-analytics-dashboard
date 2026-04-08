function togglePassword(inputId, btn) {
  const input = document.getElementById(inputId);
  if (!input) return;

  if (input.type === "password") {
    input.type = "text";
    btn.textContent = "Hide";
  } else {
    input.type = "password";
    btn.textContent = "Show";
  }
}

function generateStrongPassword() {
  const chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*";
  let password = "";
  for (let i = 0; i < 12; i++) {
    password += chars.charAt(Math.floor(Math.random() * chars.length));
  }
  return password;
}

function suggestPassword() {
  const pwd = generateStrongPassword();
  const box = document.getElementById("suggestedPassword");
  const input = document.getElementById("signupPassword");
  const confirm = document.getElementById("confirmPassword");

  if (box) box.textContent = `Suggested: ${pwd}`;
  if (input) input.value = pwd;
  if (confirm) confirm.value = pwd;
}

function validatePolicy(password) {
  const letters = (password.match(/[A-Za-z]/g) || []).length;
  const hasNumber = /\d/.test(password);
  const hasSpecial = /[!@#$%^&*()_+\-=\[\]{};:'",.<>/?\\|`~]/.test(password);

  if (letters < 4) {
    alert("Password must contain at least 4 letters.");
    return false;
  }
  if (!hasNumber) {
    alert("Password must contain at least 1 number.");
    return false;
  }
  if (!hasSpecial) {
    alert("Password must contain at least 1 special character.");
    return false;
  }
  return true;
}

function validateSignupPassword() {
  const password = document.getElementById("signupPassword")?.value || "";
  const confirm = document.getElementById("confirmPassword")?.value || "";

  if (!validatePolicy(password)) return false;

  if (password !== confirm) {
    alert("Passwords do not match.");
    return false;
  }

  return true;
}

function validateForgotPassword() {
  const password = document.getElementById("forgotPassword")?.value || "";
  const confirm = document.getElementById("forgotConfirmPassword")?.value || "";

  if (!validatePolicy(password)) return false;

  if (password !== confirm) {
    alert("Passwords do not match.");
    return false;
  }

  return true;
}