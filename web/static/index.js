const wsProtocol = location.protocol === 'https:' ? 'wss' : 'ws';
      const ws = new WebSocket(`${wsProtocol}://${location.host}/ws`);
      const messagesDiv = document.getElementById("messages");
      const statusDot = document.getElementById("status-dot");
      const fraudCountEl = document.getElementById("fraud-count");
      const msgCountEl = document.getElementById("msg-count");
      const slowBtn = document.getElementById("slow-toggle");
      const timeWindowSelect = document.getElementById("time-window");

      let messageCount = 0;
      let fraudCount = 0;
      let slowMode = false;
      let pendingDelay = 0;
      let timeWindowSec = parseInt(timeWindowSelect.value, 10);

      const ringBuffer = [];
      let totalLegit = 0;
      let totalFraud = 0;

      // Chart.js Setup
      const ctx = document.getElementById("realtimeChart").getContext("2d");
      const chart = new Chart(ctx, {
        type: "line",
        data: {
          labels: [],
          datasets: [
            {
              label: "Montant Transaction (€)",
              data: [],
              borderColor: "#4ecca3",
              backgroundColor: "rgba(78, 204, 163, 0.2)",
              borderWidth: 2,
              tension: 0.4,
              fill: true,
              pointRadius: 4,
              pointBackgroundColor: [],
            },
          ],
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            legend: { display: false },
          },
          scales: {
            x: { display: false },
            y: {
              grid: { color: "#333" },
              ticks: { color: "#b2b2b2" },
            },
          },
          animation: { duration: 0 },
        },
      });

      const distCtx = document.getElementById("distChart").getContext("2d");
      const distChart = new Chart(distCtx, {
        type: 'doughnut',
        data: {
          labels: ['LEGIT', 'FRAUD'],
          datasets: [{
            data: [0, 0],
            backgroundColor: ['#4ecca3', '#e94560'],
            borderColor: ['#2e8f76', '#a4293d'],
            borderWidth: 1
          }]
        },
        options: {
          plugins: { legend: { position: 'bottom', labels: { color: '#eaeaea' } } }
        }
      });

      function processData(data) {
        const timestamp = new Date(data.timestamp * 1000).toLocaleTimeString();

        messageCount++;
        msgCountEl.innerText = messageCount;

        if (data.status === "FRAUD") {
          fraudCount++;
          fraudCountEl.innerText = fraudCount;
        }

        const nowMs = Date.now();
        ringBuffer.push({ t: nowMs, amount: data.amount, status: data.status });
        while (ringBuffer.length && (nowMs - ringBuffer[0].t) > timeWindowSec * 1000) {
          ringBuffer.shift();
        }

        const labels = ringBuffer.map(item => new Date(item.t).toLocaleTimeString());
        const series = ringBuffer.map(item => item.amount);
        const colors = ringBuffer.map(item => item.status === 'FRAUD' ? '#ff0055' : '#4ecca3');

        chart.data.labels = labels;
        chart.data.datasets[0].data = series;
        chart.data.datasets[0].pointBackgroundColor = colors;

        chart.update();

        const messageElement = document.createElement("div");
        const isFraud = data.status === "FRAUD";
        messageElement.className = `message ${isFraud ? 'message-error' : 'message-success'}`;

        const badgeClass = isFraud ? 'badge badge-error' : 'badge badge-success';
        const label = isFraud ? 'ERROR' : 'SUCCESS';
        const statusIcon = isFraud ? '🚨' : '✅';
        const pointColor = isFraud ? '#ff0055' : '#4ecca3';

        const details = `ID: ${data.transaction_id} | Compte: ${data.account_id} | Pays: ${data.country} | Devise: ${data.currency}`;

        messageElement.innerHTML = `
          <span style="color: #b2b2b2;">[${timestamp}]</span>
          <span>${details}</span>
          <span style="color: ${pointColor}; font-weight: bold;">${statusIcon} ${data.amount} €</span>
          <span class="${badgeClass}">${label}</span>
        `;

        const detailBlock = document.createElement('div');
        detailBlock.className = 'details';
        detailBlock.textContent = JSON.stringify(data, null, 2);
        messageElement.appendChild(detailBlock);

        messageElement.addEventListener('click', () => {
          detailBlock.style.display = detailBlock.style.display === 'none' || !detailBlock.style.display ? 'block' : 'none';
        });

        messagesDiv.prepend(messageElement);
        if (messagesDiv.children.length > 50) {
          messagesDiv.removeChild(messagesDiv.lastChild);
        }

        if (isFraud) totalFraud++; else totalLegit++;
        distChart.data.datasets[0].data = [totalLegit, totalFraud];
        distChart.update();
      }

      ws.onmessage = function (event) {
        const data = JSON.parse(event.data);
        if (!slowMode) {
          processData(data);
          return;
        }
        pendingDelay = Math.min(pendingDelay + 200, 4000);
        setTimeout(() => {
          processData(data);
          pendingDelay = Math.max(pendingDelay - 200, 0);
        }, pendingDelay);
      };

      ws.onopen = () => {
        console.log("Connected");
        statusDot.className = "status-indicator status-connected";
      };

      ws.onclose = (evt) => {
        console.log("Disconnected", evt);
        statusDot.className = "status-indicator status-disconnected";
      };

      slowBtn.addEventListener('click', () => {
        slowMode = !slowMode;
        slowBtn.textContent = slowMode ? 'Désactiver Mode Lent' : 'Activer Mode Lent';
        slowBtn.classList.toggle('secondary', slowMode);
      });

      timeWindowSelect.addEventListener('change', () => {
        timeWindowSec = parseInt(timeWindowSelect.value, 10);
        const nowMs = Date.now();
        while (ringBuffer.length && (nowMs - ringBuffer[0].t) > timeWindowSec * 1000) {
          ringBuffer.shift();
        }
        const labels = ringBuffer.map(item => new Date(item.t).toLocaleTimeString());
        const series = ringBuffer.map(item => item.amount);
        const colors = ringBuffer.map(item => item.status === 'FRAUD' ? '#ff0055' : '#4ecca3');
        chart.data.labels = labels;
        chart.data.datasets[0].data = series;
        chart.data.datasets[0].pointBackgroundColor = colors;
        chart.update();
      });