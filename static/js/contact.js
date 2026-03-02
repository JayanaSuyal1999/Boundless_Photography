
const form      = document.getElementById('enquiryForm');
const errorEl   = document.getElementById('formError');
const submitBtn = form.querySelector('.form-submit');

form.addEventListener('submit', async (e) => {
  e.preventDefault();
  errorEl.textContent = '';

  const required = ['firstName', 'lastName', 'email', 'message'];
  let valid = true;
  required.forEach(id => {
    const el = document.getElementById(id);
    if (!el.value.trim()) {
      el.classList.add('error');
      valid = false;
    } else {
      el.classList.remove('error');
    }
  });
  if (!document.getElementById('consent').checked) {
    errorEl.textContent = 'Please accept the consent checkbox to continue.';
    valid = false;
  }
  if (!valid) {
    errorEl.textContent = errorEl.textContent || 'Please fill in all required fields.';
    return;
  }

  submitBtn.disabled = true;
  submitBtn.textContent = 'Sending…';

  try {
    const res = await fetch(CONTACT_API_URL, {
      method:  'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        firstName: document.getElementById('firstName').value.trim(),
        lastName:  document.getElementById('lastName').value.trim(),
        email:     document.getElementById('email').value.trim(),
        phone:     document.getElementById('phone').value.trim(),
        service:   document.getElementById('service').value,
        date:      document.getElementById('date').value,
        message:   document.getElementById('message').value.trim(),
      })
    });

    if (res.ok) {
      document.getElementById('contactFormWrap').style.display = 'none';
      document.getElementById('formSuccess').style.display = 'block';
    } else {
      const data = await res.json();
      errorEl.textContent = data.error || 'Something went wrong. Please try again.';
      submitBtn.disabled = false;
      submitBtn.textContent = 'Send Enquiry →';
    }
  } catch (err) {
    errorEl.textContent = 'Network error. Please check your connection and try again.';
    submitBtn.disabled = false;
    submitBtn.textContent = 'Send Enquiry →';
  }
});

form.querySelectorAll('input, textarea').forEach(el => {
  el.addEventListener('input', () => el.classList.remove('error'));
});

function resetForm() {
  form.reset();
  errorEl.textContent = '';
  document.getElementById('contactFormWrap').style.display = 'block';
  document.getElementById('formSuccess').style.display = 'none';
  submitBtn.disabled = false;
  submitBtn.textContent = 'Send Enquiry →';
}
