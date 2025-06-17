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

    setTimeout(() => {
    subBtn.disabled = false;
    }, 3500);

    let regex = /^(?=.*[A-Z])(?=.*\d)[A-Za-z0-9]{4,16}$/;

    if (password_str != password_check_str) {
    alert("Пароли не соответсвуют друг другу.");
    event.preventDefault();
    return;
    }

    if (!regex.test(password_str)) {
        alert("Пароль должен содержать от 4 до 16 символов, хотя бы одну заглавную букву и цифру. Запрещены * & { } | +");
        event.preventDefault();
        return;
    }

    fetch(`/register`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ login: login_str, e_mail: email_str, password: password_str }),
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            fetch(`/login`, {
            method: 'POST',
            headers: {
            'Content-Type': 'application/json'
            },
            body: JSON.stringify({ e_mail: email_str, password: password_str }),
        });
        openModal();
        document.getElementById('response-modal').innerHTML = data.message;
        }
    });
});

document.getElementById('msgModal').addEventListener('hidden.bs.modal', function () {
subBtn.disabled = true;
window.location.href = "/";});
