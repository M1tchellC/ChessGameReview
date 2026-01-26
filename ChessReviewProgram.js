async function analyze() {
  const username = document.getElementById("username").value;

  try {
    const res = await fetch("https://chessgamereview-m8hf.onrender.com/analyze", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ username }) // <- must be { "username": "..." }
    });

    if (!res.ok) {
      const errText = await res.text();
      console.error("Server returned error:", errText);
      return;
    }

    const data = await res.json();

    Plotly.newPlot("chart", [{
      x: data.move_labels,
      y: data.evaluations,
      type: "scatter"
    }]);
  } catch (err) {
    console.error("Fetch failed:", err);
  }
}


