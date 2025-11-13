// dashboard.js — ПОЛНЫЙ, с автообновлением всех таблиц

const fieldConfigs = {
  drivers: [
    { name: 'first_name', label: 'Имя', type: 'text' },
    { name: 'last_name', label: 'Фамилия', type: 'text' },
    { name: 'phone', label: 'Номер телефона', type: 'text' }
  ],
  routes: [
    { name: 'order_id', label: 'ID заказа', type: 'select', foreign: 'orders' },
    { name: 'vehicle_id', label: 'ID транспорта', type: 'select', foreign: 'vehicles' },
    { name: 'driver_id', label: 'ID водителя', type: 'select', foreign: 'drivers' },
    { name: 'departure_date', label: 'Дата отправления', type: 'date' },
    { name: 'arrival_date', label: 'Дата прибытия', type: 'date' }
  ],
  vehicles: [
    { name: 'plate_number', label: 'Номер машины', type: 'text' },
    { name: 'model', label: 'Модель', type: 'text' },
    { name: 'type', label: 'Тип', type: 'text' },
    { name: 'capacity', label: 'Вместимость', type: 'number' }
  ],
  clients: [
    { name: 'first_name', label: 'Имя', type: 'text' },
    { name: 'last_name', label: 'Фамилия', type: 'text' },
    { name: 'e_mail', label: 'E-mail', type: 'email' },
    { name: 'phone_number', label: 'Номер телефона', type: 'text' }
  ],
  orders: [
    { name: 'client_id', label: 'ID клиента', type: 'select', foreign: 'clients' },
    { name: 'order_date', label: 'Дата заказа', type: 'date' },
    { name: 'status', label: 'Статус', type: 'text' }
  ],
  warehouses: [
    { name: 'name', label: 'Название', type: 'text' },
    { name: 'address', label: 'Адрес', type: 'text' },
    { name: 'capacity', label: 'Вместимость', type: 'number' }
  ]
};

// === Формат даты ===
function formatDateToRF(dateStr) {
  if (!dateStr) return '';
  const date = new Date(dateStr);
  if (isNaN(date)) return dateStr;
  return date.toLocaleDateString('ru-RU', { day: '2-digit', month: '2-digit', year: 'numeric' });
}

function parseRFDateToISO(rfDate) {
  if (!rfDate) return '';
  const parts = rfDate.split('.');
  if (parts.length !== 3) return rfDate;
  const [day, month, year] = parts.map(p => p.trim());
  return `${year}-${month.padStart(2, '0')}-${day.padStart(2, '0')}`;
}

// === Универсальная функция обновления таблицы ===
function refreshTable(table) {
  fetchData(table);
}

// === Универсальная функция обновления всех таблиц ===
function refreshAllTables() {
  ['drivers', 'routes', 'vehicles', 'clients', 'orders', 'warehouses'].forEach(table => {
    fetchData(table);
  });
  drawOrderChart();
  drawWarehouseChart();
}

// === Модальное окно ===
let flatpickrInstances = [];

document.getElementById('universalModal').addEventListener('show.bs.modal', async function (event) {
  const button = event.relatedTarget;
  const table = button.getAttribute('data-table');
  const id = button.getAttribute('data-id') || '';
  const isEdit = button.classList.contains('edit-btn');
  const modalTitle = document.getElementById('universalModalLabel');
  const modalBody = document.getElementById('modalFormFields');
  const tableNameInput = document.getElementById('tableName');
  const editIdInput = document.getElementById('editId');

  tableNameInput.value = table;
  editIdInput.value = id;
  modalTitle.textContent = isEdit ? `Редактировать ${table}` : `Добавить ${table}`;
  modalBody.innerHTML = '';

  flatpickrInstances.forEach(fp => fp.destroy());
  flatpickrInstances = [];

  const fields = fieldConfigs[table];

  for (const field of fields) {
    const div = document.createElement('div');
    div.className = 'mb-3';

    if (field.type === 'select' && field.foreign) {
      try {
        const response = await fetch(`/api/${field.foreign}`);
        const data = await response.json();
        const options = data.map(item => {
          let text = '';
          if (field.foreign === 'clients' || field.foreign === 'drivers')
            text = `${item.first_name} ${item.last_name} (ID: ${item.id})`;
          else if (field.foreign === 'vehicles')
            text = `${item.model} – ${item.plate_number} (ID: ${item.id})`;
          else if (field.foreign === 'orders')
            text = `Заказ ${item.id} – Клиент ${item.client_id}`;
          return `<option value="${item.id}">${text}</option>`;
        }).join('');

        div.innerHTML = `
          <label for="${field.name}" class="form-label">${field.label}</label>
          <select class="form-select select-search" id="${field.name}">
            <option value="">— Выберите —</option>
            ${options}
          </select>
        `;
      } catch (err) {
        div.innerHTML = `<p class="text-danger">Ошибка загрузки</p>`;
      }
    }
    else if (field.type === 'date') {
      div.innerHTML = `
        <label for="${field.name}" class="form-label">${field.label}</label>
        <input type="text" class="form-control flatpickr-input" id="${field.name}" placeholder="ДД.ММ.ГГГГ">
      `;
    }
    else {
      div.innerHTML = `
        <label for="${field.name}" class="form-label">${field.label}</label>
        <input type="${field.type}" class="form-control" id="${field.name}">
      `;
    }
    modalBody.appendChild(div);
  }

  setTimeout(() => {
    $('.select-search').select2({
      placeholder: 'Поиск...',
      allowClear: true,
      width: '100%',
      theme: 'bootstrap-5'
    });
  }, 100);

  setTimeout(() => {
    document.querySelectorAll('.flatpickr-input').forEach(input => {
      const fp = flatpickr(input, {
        locale: 'ru',
        dateFormat: 'd.m.Y',
        allowInput: true,
        clickOpens: true
      });
      flatpickrInstances.push(fp);
    });
  }, 150);

  if (isEdit && id) {
    try {
      const response = await fetch(`/api/${table}/${id}`);
      const data = await response.json();

      fields.forEach(field => {
        const el = document.getElementById(field.name);
        if (!el) return;

        if (field.type === 'date') {
          el.value = formatDateToRF(data[field.name]);
          const fp = el._flatpickr;
          if (fp) fp.setDate(el.value, false);
        } else if (field.type === 'select') {
          el.value = data[field.name] || '';
          $(el).trigger('change');
        } else {
          el.value = data[field.name] || '';
        }
      });
    } catch (err) {
      console.error('Ошибка загрузки:', err);
    }
  }
});

document.getElementById('universalModal').addEventListener('hidden.bs.modal', function () {
  $('.select-search').select2('destroy');
  flatpickrInstances.forEach(fp => fp.destroy());
  flatpickrInstances = [];
});

// === Загрузка данных ===
async function fetchData(table) {
  try {
    const response = await fetch(`/api/${table}`);
    if (!response.ok) throw new Error('Network error');
    const data = await response.json();
    populateTable(table, data);
  } catch (error) {
    console.error(`Ошибка загрузки ${table}:`, error);
  }
}

function populateTable(table, data) {
  const tbody = document.getElementById(`${table}Table`)?.querySelector('tbody');
  if (!tbody) return;
  tbody.innerHTML = '';

  data.forEach(entry => {
    const row = document.createElement('tr');
    const idCell = document.createElement('td');
    idCell.textContent = entry.id || '—';
    row.appendChild(idCell);

    fieldConfigs[table].forEach(field => {
      const cell = document.createElement('td');
      if (field.type === 'date' && entry[field.name]) {
        cell.textContent = formatDateToRF(entry[field.name]);
      } else {
        cell.textContent = entry[field.name] || '—';
      }
      row.appendChild(cell);
    });

    const actionCell = document.createElement('td');
    actionCell.className = 'actions-cell';
    actionCell.innerHTML = `
      <button class="btn btn-sm btn-primary edit-btn" data-bs-toggle="modal" data-bs-target="#universalModal" data-table="${table}" data-id="${entry.id}">🖉</button>
      <button class="btn btn-sm btn-danger" onclick="deleteEntry('${table}', ${entry.id})">🗑</button>
    `;
    if (table === 'orders') {
      actionCell.innerHTML += `
        <button class="btn btn-sm btn-warning manage-warehouses-btn" data-id="${entry.id}">Склады</button>
      `;
    }
    row.appendChild(actionCell);
    tbody.appendChild(row);
  });

  if ($.fn.DataTable.isDataTable(`#${table}Table`)) {
    $(`#${table}Table`).DataTable().destroy();
  }
  $(`#${table}Table`).DataTable({
    paging: true, searching: true, ordering: true, info: true,
    lengthMenu: [5, 10, 25, 50],
    language: {
      search: 'Поиск:', lengthMenu: 'Показать _MENU_',
      info: 'Записи _START_–_END_ из _TOTAL_',
      paginate: { first: 'Первая', last: 'Последняя', next: 'Вперёд', previous: 'Назад' }
    }
  });
}

// === Сохранение — обновляем ВСЕ таблицы ===
async function saveEntry() {
  const table = document.getElementById('tableName').value;
  const id = document.getElementById('editId').value;
  const data = {};

  fieldConfigs[table].forEach(field => {
    const el = document.getElementById(field.name);
    if (!el) return;
    let value = el.value;
    if (field.type === 'date' && value) {
      value = parseRFDateToISO(value);
    }
    data[field.name] = value;
  });

  const method = id ? 'PUT' : 'POST';
  const url = id ? `/api/${table}/${id}` : `/api/${table}`;

  try {
    const response = await fetch(url, {
      method,
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    });
    if (response.ok) {
      bootstrap.Modal.getInstance(document.getElementById('universalModal')).hide();
      refreshAllTables(); // Обновляем ВСЁ
    } else {
      alert('Ошибка сохранения');
    }
  } catch (error) {
    console.error('Ошибка:', error);
  }
}

// === Удаление — обновляем ВСЁ ===
async function deleteEntry(table, id) {
  if (!confirm('Удалить запись?')) return;
  try {
    const response = await fetch(`/api/${table}/${id}`, { method: 'DELETE' });
    if (response.ok) {
      refreshAllTables(); // Обновляем ВСЁ
    } else {
      alert('Ошибка удаления');
    }
  } catch (error) {
    console.error('Ошибка:', error);
  }
}

// === Управление складами — обновляем таблицы и склады ===
let currentOrderId = null;
let allWarehouses = [];

async function loadWarehouses() {
  try {
    const response = await fetch('/api/warehouses');
    allWarehouses = await response.json();
  } catch (err) {
    console.error('Ошибка:', err);
  }
}
loadWarehouses();

document.querySelector('.tab-content').addEventListener('click', function (e) {
  if (e.target.classList.contains('manage-warehouses-btn')) {
    currentOrderId = e.target.dataset.id;
    populateWarehouseSelect();
    fetchAssociatedWarehouses();
    new bootstrap.Modal(document.getElementById('manageWarehousesModal')).show();
  }
});

function populateWarehouseSelect() {
  const select = document.getElementById('warehouseSelect');
  select.innerHTML = allWarehouses.map(w =>
    `<option value="${w.id}">${w.name} (${w.address})</option>`
  ).join('');
}

async function fetchAssociatedWarehouses() {
  try {
    const response = await fetch(`/api/warehouses_orders/${currentOrderId}`);
    const data = await response.json();
    const ul = document.getElementById('associatedWarehouses');
    ul.innerHTML = data.map(w => `
      <li class="list-group-item d-flex justify-content-between align-items-center">
        ${w.name} (${w.address})
        <button class="btn btn-sm btn-danger" onclick="deleteWarehouseFromOrder(${w.id})">Удалить</button>
      </li>
    `).join('');
  } catch (err) {
    console.error('Ошибка:', err);
  }
}

async function addWarehouseToOrder() {
  const warehouseId = document.getElementById('warehouseSelect').value;
  if (!warehouseId) return;
  try {
    const response = await fetch(`/api/warehouses_orders/${currentOrderId}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ warehouse_id: warehouseId })
    });
    if (response.ok) {
      fetchAssociatedWarehouses();
      refreshAllTables(); // Обновляем таблицы
    }
  } catch (err) {
    console.error('Ошибка:', err);
  }
}

async function deleteWarehouseFromOrder(warehouseId) {
  try {
    const response = await fetch(`/api/warehouses_orders/${currentOrderId}`, {
      method: 'DELETE',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ warehouse_id: warehouseId })
    });
    if (response.ok) {
      fetchAssociatedWarehouses();
      refreshAllTables(); // Обновляем таблицы
    }
  } catch (err) {
    console.error('Ошибка:', err);
  }
}

// === Диаграммы ===
function drawOrderChart() {
  d3.select("#orderChart").selectAll("*").remove();
  const width = 400, height = 300, radius = Math.min(width, height) / 2;
  fetch('/api/orders')
    .then(r => r.json())
    .then(orders => {
      const statusCount = {};
      orders.forEach(o => statusCount[o.status] = (statusCount[o.status] || 0) + 1);
      const data = Object.entries(statusCount);

      const svg = d3.select("#orderChart")
        .append("svg")
        .attr("width", width)
        .attr("height", height)
        .append("g")
        .attr("transform", `translate(${width / 2}, ${height / 2})`);

      const color = d3.scaleOrdinal(d3.schemeCategory10);
      const pie = d3.pie().value(d => d[1]);
      const arc = d3.arc().innerRadius(0).outerRadius(radius - 10);

      svg.selectAll("path")
        .data(pie(data))
        .enter()
        .append("path")
        .attr("d", arc)
        .attr("fill", d => color(d.data[0]))
        .attr("stroke", "white")
        .attr("stroke-width", 2);

      svg.selectAll("text")
        .data(pie(data))
        .enter()
        .append("text")
        .attr("transform", d => `translate(${arc.centroid(d)})`)
        .attr("dy", ".35em")
        .attr("text-anchor", "middle")
        .text(d => d.data[0]);
    });
}

function drawWarehouseChart() {
  d3.select("#warehouseChart").selectAll("*").remove();
  const width = 400, height = 300, margin = { top: 20, right: 20, bottom: 40, left: 50 };
  const chartWidth = width - margin.left - margin.right;
  const chartHeight = height - margin.top - margin.bottom;

  const svg = d3.select("#warehouseChart")
    .append("svg")
    .attr("width", width)
    .attr("height", height)
    .append("g")
    .attr("transform", `translate(${margin.left},${margin.top})`);

  fetch('/api/warehouses')
    .then(r => r.json())
    .then(warehouses => {
      const x = d3.scaleBand()
        .domain(warehouses.map(w => w.name))
        .range([0, chartWidth])
        .padding(0.1);
      const y = d3.scaleLinear()
        .domain([0, d3.max(warehouses, w => w.capacity)])
        .range([chartHeight, 0]);

      svg.append("g")
        .attr("transform", `translate(0,${chartHeight})`)
        .call(d3.axisBottom(x));
      svg.append("g")
        .call(d3.axisLeft(y));

      svg.selectAll(".bar")
        .data(warehouses)
        .enter()
        .append("rect")
        .attr("class", "bar")
        .attr("x", d => x(d.name))
        .attr("y", d => y(d.capacity))
        .attr("width", x.bandwidth())
        .attr("height", d => chartHeight - y(d.capacity))
        .attr("fill", "#007bff");
    });
}

// === Запуск ===
refreshAllTables();