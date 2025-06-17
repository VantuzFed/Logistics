function openModal() {
    var myModal = new bootstrap.Modal(document.getElementById('msgAdminModal'));
    myModal.show();
}

function renderStats() {
    const container = document.getElementById("stats-block");
    container.innerHTML = "";

    fetch(`/api/admin`)
        .then(response => response.json())
        .then(data => {
            const { orders_count, users_count, valid_session, sessions_per_user } = data;

            const statsHTML = `
                <p>Всего заказов: ${orders_count}</p>
                <p>Всего пользователей: ${users_count}</p>
                <p>Активные сессии: ${valid_session}</p>
                <h3>Сессии пользователей:</h3>
                    ${sessions_per_user.map(user => `<p>${user.user_login}: ${user.sessions_count} сессий</p>`).join('')}
            `;

            container.innerHTML = statsHTML;
        })
        .catch(error => {
            console.error("Ошибка загрузки статистики:", error);
            container.innerHTML = "<p>Ошибка загрузки данных</p>";
        });
}

function renderUsers() {
    const container = document.getElementById("manage-block");
    container.innerHTML = "";

    fetch(`/api/admin/users`)
        .then(response => response.json())
        .then(data => {
    data.forEach(user => {
        const cardHTML = `
            <tr>
      <th scope="row">${user.id}</th>
      <td>${user.login}</td>
      <td>${user.e_mail}</td>
      <td>${user.account_type}</td>
      <td><button class="btn btn-primary" data-id="${user.id}">Сбросить пароль</button></td>
      <td><form id="user-rights-form-${user.id}">
  <select id="user-rights-${user.id}" name="user-rights-${user.id}">
    <option value="User">User</option>
    <option value="Admin">Admin</option>
  </select>
<button class="btn btn-success" type="submit" data-id="${user.id}">Сохранить</button>
</form></td>
      <td><button class="btn btn-danger" data-id="${user.id}">Удалить пользователя</button></td>
    </tr>`;
        container.innerHTML += cardHTML;
    });
        })
        .catch(error => {
            console.error("Ошибка загрузки:", error);
            container.innerHTML = "<p>Ошибка загрузки данных</p>";
        });
}

document.addEventListener("DOMContentLoaded", function() {
    document.getElementById("manage-block").addEventListener("submit", function(event) {
        if (event.target.tagName === "FORM" && event.target.id.startsWith("user-rights-form-")) {
            event.preventDefault();

            const userId = event.target.querySelector("button").dataset.id;
            const selectedRole = document.getElementById(`user-rights-${userId}`).value;

            fetch(`/api/admin/users/${userId}`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ account_type: selectedRole})
            })
            .then(response => response.json())
            .then(data => {
            openModal();
            document.getElementById('response-modal').innerHTML = data.message;
                if (data.success) {
                    renderUsers();
                }
            })
            .catch(error => console.error("Ошибка изменения прав пользователя:", error));
        }
    });


    document.getElementById("manage-block").addEventListener("click", function(event) {
        if (event.target.classList.contains("btn-danger")) {
        if (!confirm('Вы уверены, что хотите удалить этого пользователя?')){
            return;
        }
            const userId = event.target.dataset.id;

            fetch(`/api/admin/users/${userId}`, {
                method: 'DELETE',
                headers: {
                    'Content-Type': 'application/json'
                }
            })
            .then(response => response.json())
            .then(data => {
                openModal();
                document.getElementById('response-modal').innerHTML = data.message;
                if (data.success) {
                    renderUsers();
                }
            })
            .catch(error => console.error("Ошибка удаления пользователя:", error));
        }
    });

    document.getElementById("manage-block").addEventListener("click", function(event) {
        if (event.target.classList.contains("btn-primary")) {
            const userId = event.target.dataset.id;

            fetch(`/api/admin/users/${userId}`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ reset_password: true })
            })
            .then(response => response.json())
            .then(data => {
                openModal();
                document.getElementById('response-modal').innerHTML = `<p>${data.message}:</p><p>${data.new_password}</p>`;
            })
            .catch(error => console.error("Ошибка сброса пароля:", error));
        }
    });

});

renderStats();
renderUsers();