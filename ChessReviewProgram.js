async function analyze() {
  const username = document.getElementById("username").value;

  try {
    const res = await fetch("https://chessgamereview-m8hf.onrender.com/analyze", { //Get data from Render Server
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

    const moves = data.evaluations.map((_, i) => i + 1); //Calculate total moves

    let evals = data.evaluations;
    
    if (data.you.color === "black") { //Plot advantage based on which color you played
      evals = evals.map(v => -v);
    }
    Plotly.newPlot(
      "chart", 
      [{ //Plot centipawn advantage
        x: moves,
        y: evals,
        type: "scatter",
        mode: "lines+markers",
        name: "Centipawn Advantage"
    }], 
      {
        title: "Centipawn Advantage Over Time",
        xaxis: { title: "Move Number" },
        yaxis: { title: "Evaluation (pawns)" }
      }
    );
    const breakdownDiv = document.getElementById("breakdown"); //Plot how many of each move tyoe was made (Good, Great, etc...)
    const b = data.move_breakdown;
    
    breakdownDiv.innerHTML = `
    <h3>Move Quality Breakdown</h3>
    <ul>
      <li>${username} played: ${data.you.color}</li>
      <li>White Best: ${b.wtotBest}</li>
      <li>White Excellent: ${b.wtotExcellent}</li>
      <li>White Great: ${b.wtotGreat}</li>
      <li>White Good: ${b.wtotGood}</li>
      <li>White Inaccuracy: ${b.wtotInaccuracy}</li>
      <li>White Mistake: ${b.wtotMistake}</li>
      <li>White Blunder: ${b.wtotBlunder}</li>
      <br/>
      <li>Black Best: ${b.btotBest}</li>
      <li>Black Excellent: ${b.btotExcellent}</li>
      <li>Black Great: ${b.btotGreat}</li>
      <li>Black Good: ${b.btotGood}</li>
      <li>Black Inaccuracy: ${b.btotInaccuracy}</li>
      <li>Black Mistake: ${b.btotMistake}</li>
      <li>Black Blunder: ${b.btotBlunder}</li>
    </ul>
    `;
  } catch (err) {
    console.error("Fetch failed:", err);
  }
}





