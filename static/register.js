function openModal() {
  var myModal = new bootstrap.Modal(document.getElementById('msgModal'));
  myModal.show();
}

let subBtn = document.getElementById('sub-btn');

document.getElementById("RegForm").addEventListener("submit", async function(event) {
  event.preventDefault();
  const login_str = document.getElementById('login').value;
  const email_str = document.getElementById('email').value;
  const password_str = document.getElementById('password').value;
  const password_check_str = document.getElementById('password-check').value;

  subBtn.disabled = true;

  const regex = /^(?=.*[A-Z])(?=.*\d)[A-Za-z\d]{4,16}$/; // Фикс: убрал ненужные, запрет спецсимволов

  if (password_str !== password_check_str) {
    alert("Пароли не соответствуют друг другу.");
    subBtn.disabled = false;
    return;
  }

  if (!regex.test(password_str)) {
    alert("Пароль должен содержать от 4 до 16 символов (A-Za-z0-9), хотя бы одну заглавную букву и цифру. Спецсимволы запрещены.");
    subBtn.disabled = false;
    return;
  }

  try {
    const regResponse = await fetch(`/register`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ login: login_str, e_mail: email_str, password: password_str }),
    });
    const regData = await regResponse.json();
    openModal();
    document.getElementById('response-modal').innerHTML = regData.message;

    if (regData.success) {
      // Фикс: добавили .then для login
      await fetch(`/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ e_mail: email_str, password: password_str }),
      }).then(loginResponse => loginResponse.json())
        .then(loginData => {
          if (!loginData.success) throw new Error('Автологин failed');
        });

      const modalEl = document.getElementById('msgModal');
      modalEl.addEventListener('hidden.bs.modal', function () {
        window.location.href = "/";
      }, { once: true });
    } else {
      subBtn.disabled = false;
    }
  } catch (error) {
    console.error('Ошибка:', error);
    openModal();
    document.getElementById('response-modal').innerHTML = 'Ошибка регистрации';
    subBtn.disabled = false;
  }
});