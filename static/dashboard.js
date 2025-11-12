 // Field configurations for each table
    const fieldConfigs = {
      drivers: [
        { name: 'first_name', label: 'Имя', type: 'text' },
        { name: 'last_name', label: 'Фамилия', type: 'text' },
        { name: 'phone', label: 'Номер телефона', type: 'text' }
      ],
      routes: [
        { name: 'order_id', label: 'ID заказа', type: 'number' },
        { name: 'vehicle_id', label: 'ID транспорта', type: 'number' },
        { name: 'driver_id', label: 'ID водителя', type: 'number' },
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
        { name: 'client_id', label: 'ID клиента', type: 'text' },
        { name: 'order_date', label: 'Дата заказа', type: 'date' },
        { name: 'status', label: 'Статус', type: 'text' }
      ],
      warehouses: [
        { name: 'name', label: 'Название', type: 'text' },
        { name: 'address', label: 'Адрес', type: 'text' },
        { name: 'capacity', label: 'Вместимость', type: 'number' }
      ]
    };

    // Populate modal fields dynamically
    document.getElementById('universalModal').addEventListener('show.bs.modal', function (event) {
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
      modalTitle.textContent = isEdit ? `Edit ${table.charAt(0).toUpperCase() + table.slice(1)}` : `Добавить ${table.charAt(0).toUpperCase() + table.slice(1)}`;
      modalBody.innerHTML = '';

      const fields = fieldConfigs[table];
      fields.forEach(field => {
        const div = document.createElement('div');
        div.className = 'mb-3';
        div.innerHTML = `
          <label for="${field.name}" class="form-label">${field.label}</label>
          <input type="${field.type}" class="form-control" id="${field.name}" name="${field.name}">
        `;
        modalBody.appendChild(div);
      });

      if (isEdit && id) {
        fetchData(table, id, (data) => {
          fields.forEach(field => {
            const input = document.getElementById(field.name);
            input.value = data[field.name] || '';
          });
        });
      }
    });

    // AJAX functions
    function fetchData(table, id = null, callback) {
      const url = id ? `/api/${table}/${id}` : `/api/${table}`;
      fetch(url)
        .then(response => response.json())
        .then(data => {
          if (id) callback(data);
          else populateTable(table, data);
        })
        .catch(error => console.error('Ошибка получения данных:', error));
    }

    function saveEntry() {
      const table = document.getElementById('tableName').value;
      const id = document.getElementById('editId').value;
      const fields = fieldConfigs[table];
      const data = {};
      fields.forEach(field => {
        data[field.name] = document.getElementById(field.name).value;
      });

      const method = id ? 'PUT' : 'POST';
      const url = id ? `/api/${table}/${id}` : `/api/${table}`;

      fetch(url, {
        method: method,
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
      })
        .then(response => response.json())
        .then(() => {
          fetchData(table);
          if (table === 'orders') drawOrderChart();
          if (table === 'warehouses') drawWarehouseChart();
          document.getElementById('universalModal').querySelector('.btn-close').click();
        })
        .catch(error => console.error('Ошибка сохранения данных:', error));
    }

    function deleteEntry(table, id) {
      if (confirm(`Вы уверены что хотите удалить эту ${table} запись?`)) {
        fetch(`/api/${table}/${id}`, {
          method: 'DELETE'
        })
          .then(response => response.json())
          .then(() => {
            fetchData(table);
            if (table === 'orders') drawOrderChart();
            if (table === 'warehouses') drawWarehouseChart();
          })
          .catch(error => console.error('Error deleting data:', error));
      }
    }


    function populateTable(table, data) {
      const tbody = document.querySelector(`#${table}Table tbody`);
      tbody.innerHTML = '';
      data.forEach(item => {
        const row = document.createElement('tr');
        const idCell = document.createElement('td');
        idCell.textContent = item.id;
        row.appendChild(idCell);
        const fields = fieldConfigs[table];
        fields.forEach(field => {
          const cell = document.createElement('td');
          cell.textContent = item[field.name];
          row.appendChild(cell);
        });
        const actionCell = document.createElement('td');
        actionCell.innerHTML = `
          <button class="btn btn-warning edit-btn" data-bs-toggle="modal" data-bs-target="#universalModal" data-table="${table}" data-id="${item.id}">🖉</button>
          <button class="btn btn-danger delete-btn" onclick="deleteEntry('${table}', ${item.id})">🗑</button>
        `;
        row.appendChild(actionCell);
        tbody.appendChild(row);
      });
    }


    ['drivers', 'routes', 'vehicles', 'clients', 'orders', 'warehouses'].forEach(table => {
      fetchData(table);
    });


    function drawOrderChart() {
      d3.select("#orderChart").selectAll("*").remove();
      const width = 400, height = 300, radius = Math.min(width, height) / 2;
      fetch('/api/orders')
        .then(response => response.json())
        .then(orders => {
          const statusCount = {};
          orders.forEach(o => {
            statusCount[o.status] = (statusCount[o.status] || 0) + 1;
          });
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
        .then(response => response.json())
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

    drawOrderChart();
    drawWarehouseChart();