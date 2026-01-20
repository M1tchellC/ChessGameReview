async function analyze() {
  const username = document.getElementById("username").value;

  const res = await fetch("https://chessgamereview-m8hf.onrender.com/analyze", {
    method: "POST",
    headers: {"Content-Type": "application/json"},
    body: JSON.stringify({ username })
  });

  const data = await res.json();

  Plotly.newPlot("chart", [{
    x: data.move_labels,
    y: data.evaluations,
    type: "scatter"
  }]);
}
