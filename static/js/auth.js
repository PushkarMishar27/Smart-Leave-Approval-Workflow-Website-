/* ==========================================================================
   SmartLeave Authentication JavaScript (Role Login, TOTP MFA 6-box OTP)
   ========================================================================== */

let selectedRole = 'Student/Employee';

document.addEventListener('DOMContentLoaded', () => {
    initRoleTabs();
    initOtpInputs();
    initPasswordToggle();
});

function initRoleTabs() {
    const roleBtns = document.querySelectorAll('.role-tab-btn');
    roleBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            roleBtns.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            selectedRole = btn.dataset.role;

            const label = document.getElementById('employee-id-label');
            if (label) {
                if (selectedRole === 'Faculty/Approver') {
                    label.innerText = 'Staff / Faculty ID';
                } else if (selectedRole === 'Admin') {
                    label.innerText = 'Admin ID';
                } else {
                    label.innerText = 'College / Employee ID';
                }
            }
        });
    });
}

function initPasswordToggle() {
    const toggleBtn = document.getElementById('toggle-password-btn');
    const pwdInput = document.getElementById('password-input');
    if (toggleBtn && pwdInput) {
        toggleBtn.addEventListener('click', () => {
            const isPwd = pwdInput.type === 'password';
            pwdInput.type = isPwd ? 'text' : 'password';
            toggleBtn.innerHTML = isPwd ? '<i class="fas fa-eye-slash"></i>' : '<i class="fas fa-eye"></i>';
        });
    }
}

function fillDemoAccount(role) {
    const empInput = document.getElementById('employee-id-input');
    const pwdInput = document.getElementById('password-input');
    
    if (role === 'Student') {
        selectedRole = 'Student/Employee';
        if (empInput) empInput.value = 'STU1001';
    } else if (role === 'Faculty') {
        selectedRole = 'Faculty/Approver';
        if (empInput) empInput.value = 'FAC2001';
    } else if (role === 'Admin') {
        selectedRole = 'Admin';
        if (empInput) empInput.value = 'ADM3001';
    }
    if (pwdInput) pwdInput.value = 'password123';
    showToast(`Filled Demo credentials for ${role}`, 'info');
}

function initOtpInputs() {
    const otpBoxes = document.querySelectorAll('.otp-box');
    otpBoxes.forEach((box, idx) => {
        box.addEventListener('keyup', (e) => {
            if (e.key >= '0' && e.key <= '9') {
                box.value = e.key;
                if (idx < otpBoxes.length - 1) {
                    otpBoxes[idx + 1].focus();
                }
            } else if (e.key === 'Backspace') {
                box.value = '';
                if (idx > 0) {
                    otpBoxes[idx - 1].focus();
                }
            }
        });

        box.addEventListener('paste', (e) => {
            const pasteData = e.clipboardData.getData('text').trim();
            if (pasteData.length === 6 && /^\d+$/.test(pasteData)) {
                otpBoxes.forEach((b, i) => b.value = pasteData[i]);
                e.preventDefault();
            }
        });
    });
}

async function handleLoginSubmit(e) {
    e.preventDefault();
    const empId = document.getElementById('employee-id-input').value;
    const password = document.getElementById('password-input').value;
    const btn = document.getElementById('login-submit-btn');

    if (!empId || !password) {
        showToast('Please enter your ID and password.', 'warning');
        return;
    }

    btn.disabled = true;
    btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Verifying...';

    try {
        const res = await fetch('/api/auth/login', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ employee_id: empId, password: password })
        });
        const data = await res.json();

        if (data.success && data.requires_mfa) {
            showToast(data.message, 'success');
            // Show MFA Step
            document.getElementById('login-step-1').style.display = 'none';
            document.getElementById('mfa-step-2').style.display = 'block';
            startOtpCountdown();
        } else {
            showToast(data.message || 'Login failed', 'danger');
        }
    } catch (err) {
        showToast('Network error during login.', 'danger');
    } finally {
        btn.disabled = false;
        btn.innerHTML = 'Continue to MFA <i class="fas fa-arrow-right"></i>';
    }
}

let countdownTimer;
function startOtpCountdown() {
    let seconds = 30;
    const timerElem = document.getElementById('otp-timer');
    if (timerElem) {
        clearInterval(countdownTimer);
        countdownTimer = setInterval(() => {
            seconds--;
            timerElem.innerText = `Code expires in ${seconds}s`;
            if (seconds <= 0) {
                seconds = 30;
            }
        }, 1000);
    }
}

async function handleMfaVerify(e) {
    e.preventDefault();
    const otpBoxes = document.querySelectorAll('.otp-box');
    let otpCode = '';
    otpBoxes.forEach(b => otpCode += b.value);

    if (otpCode.length !== 6) {
        showToast('Please enter complete 6-digit MFA verification code.', 'warning');
        return;
    }

    const btn = document.getElementById('mfa-verify-btn');
    btn.disabled = true;
    btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Verifying Code...';

    try {
        const res = await fetch('/api/auth/verify-mfa', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ otp_code: otpCode })
        });
        const data = await res.json();

        if (data.success) {
            showToast('Authentication successful! Redirecting...', 'success');
            setTimeout(() => {
                window.location.href = data.redirect_url;
            }, 800);
        } else {
            showToast(data.message || 'Verification failed.', 'danger');
        }
    } catch (err) {
        showToast('Network error during MFA verification.', 'danger');
    } finally {
        btn.disabled = false;
        btn.innerHTML = 'Verify & Continue <i class="fas fa-check"></i>';
    }
}
