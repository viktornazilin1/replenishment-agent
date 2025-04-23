import "@ui5/webcomponents/dist/Assets.js";
import "@ui5/webcomponents-fiori/dist/Assets.js";
import "@ui5/webcomponents-localization/dist/Assets.js";
import Chart from "chart.js/auto";
import "@ui5/webcomponents/dist/Select.js";
import "@ui5/webcomponents/dist/Option.js";
import "@ui5/webcomponents/dist/Button.js";
import "@ui5/webcomponents/dist/Card.js";
import "@ui5/webcomponents/dist/Label.js";

const materialSelect = document.getElementById("materialSelect");
const storeSelect = document.getElementById("storeSelect");
const forecastTableDiv = document.getElementById("forecastTableDiv");

fetch("/api/materials")
  .then(res => res.json())
  .then(materials => {
    materials.forEach(mat => {
      const option = document.createElement("ui5-option");
      option.value = mat.material_id;
      option.textContent = mat.description;
      materialSelect.appendChild(option);
    });
  });

fetch("/api/stores")
  .then(res => res.json())
  .then(stores => {
    stores.forEach(store => {
      const option = document.createElement("ui5-option");
      option.value = store.store_id;
      option.textContent = store.store_name;
      storeSelect.appendChild(option);
    });
  });

document.getElementById("submitBtn").addEventListener("click", async () => {
  const material_id = materialSelect.value;
  const store_id = storeSelect.value;
  const analysis_type = document.getElementById("analysisType").value;

  const response = await fetch("/api/forecast", {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify({ material_id, store_id, analysis_type })
  });

  const result = await response.json();

  let message = `🔮 <b>Прогноз спроса на 7 дней:</b> ${result.predicted_demand}<br>
📦 <b>Текущий остаток:</b> ${result.current_stock}<br>
🚚 <b>Рекомендуемое пополнение:</b> ${result.suggested_qty}<br>`;

  if (result.model_used === false) {
    message += `<br>⚠ Использован упрощённый прогноз — данных для модели было недостаточно.`;
  }

  if (result.has_shortage) {
    message += `<br><span style="color:red;">❗ Возможен дефицит! Требуется пополнение.</span>`;
  } else {
    message += `<br><span style="color:green;">✅ Запас достаточен.</span>`;
  }

  document.getElementById("forecastLabel").innerHTML = message;
  document.getElementById("resultCard").style.display = "block";

  // Очистим блок перед новым выводом
  forecastTableDiv.innerHTML = result.forecast_table_html || "";

  // ➕ Добавим информацию о том, какие данные использовались
  const dataUsed = result.data_used || {};
  let usedInfo = "<br><h4>📊 Использованные данные:</h4><ul>";
  if (dataUsed.weather_used) usedInfo += "<li>🌤 Погодные данные</li>";
  if (dataUsed.holidays_used) usedInfo += "<li>🎉 Праздники</li>";
  if (dataUsed.promotions_used) usedInfo += "<li>🏷 Промоакции</li>";
  if (!dataUsed.weather_used && !dataUsed.holidays_used && !dataUsed.promotions_used)
    usedInfo += "<li>📈 Только история продаж</li>";
  usedInfo += "</ul>";
  forecastTableDiv.insertAdjacentHTML("beforeend", usedInfo);

  // 📊 Построение графика
  const ctx = document.getElementById("forecastChart").getContext("2d");
  document.getElementById("forecastChart").style.display = "block";

  if (window.forecastChart instanceof Chart) {
    window.forecastChart.destroy();
  }

  window.forecastChart = new Chart(ctx, {
    type: "bar",
    data: {
      labels: ["Прогноз", "Остаток", "К пополнению"],
      datasets: [{
        label: "Значения",
        data: [
          result.predicted_demand,
          result.current_stock,
          result.suggested_qty
        ],
        backgroundColor: [
          "rgba(75, 192, 192, 0.6)",
          "rgba(255, 206, 86, 0.6)",
          "rgba(255, 99, 132, 0.6)"
        ],
        borderColor: [
          "rgba(75, 192, 192, 1)",
          "rgba(255, 206, 86, 1)",
          "rgba(255, 99, 132, 1)"
        ],
        borderWidth: 1
      }]
    },
    options: {
      responsive: true,
      plugins: {
        legend: { display: false },
        title: {
          display: true,
          text: 'Прогноз пополнения'
        }
      },
      scales: {
        y: {
          beginAtZero: true
        }
      }
    }
  });

  // ✅ Показать кнопку "Создать заявку", если есть дефицит
  const orderBtnId = "createOrderBtn";
  let orderBtn = document.getElementById(orderBtnId);

  if (!orderBtn) {
    orderBtn = document.createElement("ui5-button");
    orderBtn.id = orderBtnId;
    orderBtn.textContent = "Создать заявку на закупку";
    orderBtn.setAttribute("design", "Positive");
    orderBtn.style.marginTop = "1rem";
    forecastTableDiv.appendChild(orderBtn);
  }

  orderBtn.style.display = result.has_shortage ? "inline-block" : "none";
  orderBtn.onclick = async () => {
    const res = await fetch("/api/purchase-order", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        material_id,
        store_id,
        qty: result.suggested_qty
      })
    });
    const data = await res.json();
    alert(data.message || "Заявка создана.");
  };
});

if (result.city) {
  message += `<br>🌍 <b>Геолокация магазина:</b> ${result.city} (${result.latitude}, ${result.longitude})`;
}
if (result.data_used?.weather_used) {
  message += `<br>🌦 <b>Погодные данные были использованы в прогнозе.</b>`;
}
