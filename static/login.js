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

    setTimeout(() => {
    subBtn.disabled = false;
    }, 3500);

    fetch(`/login`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ e_mail: email_str, password: password_str }),
    })
    .then(response => response.json())
    .then(data => {
        openModal();
        document.getElementById('response-modal').innerHTML = data.message;
        if (data.success) {
        document.getElementById('msgModal').addEventListener('hidden.bs.modal', function () {
        subBtn.disabled = true;
        window.location.href = "/";});
        }
    });
});


