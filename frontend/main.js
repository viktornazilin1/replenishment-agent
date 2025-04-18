
import "@ui5/webcomponents/dist/Select.js";
import "@ui5/webcomponents/dist/Option.js";
import "@ui5/webcomponents/dist/Button.js";
import "@ui5/webcomponents/dist/Card.js";
import "@ui5/webcomponents/dist/Label.js";

const materialSelect = document.getElementById("materialSelect");
const storeSelect = document.getElementById("storeSelect");

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

  if (result.forecast_table_html) {
    document.getElementById("forecastTableDiv").innerHTML = result.forecast_table_html;
  }

  if (result.plot_path) {
    const plotImg = document.getElementById("forecastPlotImg");
    plotImg.src = result.plot_path;
    plotImg.style.display = "block";
  }
});
