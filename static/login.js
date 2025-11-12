function openModal() {
  var myModal = new bootstrap.Modal(document.getElementById('msgModal'));
  myModal.show();
}

let subBtn = document.getElementById('sub-btn');

document.getElementById("LogForm").addEventListener("submit", async function(event) {
  event.preventDefault();
  const email_str = document.getElementById('email').value;
  const password_str = document.getElementById('password').value;

  subBtn.disabled = true;

  try {
    const response = await fetch(`/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ e_mail: email_str, password: password_str }),
    });
    const data = await response.json();
    openModal();
    document.getElementById('response-modal').innerHTML = data.message;
    if (data.success) {
      const modalEl = document.getElementById('msgModal');
      modalEl.addEventListener('hidden.bs.modal', function () {
        window.location.href = "/";
      }, { once: true }); // once: чтобы не дублировать
    } else {
      subBtn.disabled = false;
    }
  } catch (error) {
    console.error('Ошибка:', error);
    openModal();
    document.getElementById('response-modal').innerHTML = 'Ошибка соединения';
    subBtn.disabled = false;
  }
});