// server.js
const express = require('express');
const { exec } = require('child_process');
const cors = require('cors');
const app = express();
const PORT = 3000;

app.use(cors());
app.use(express.static('public')); // assuming HTML/JS/CSS are in /public

app.post('/start-match', (req, res) => {
  exec('bash ai-analisis.sh', (err, stdout, stderr) => {
    if (err) return res.status(500).send(`Error: ${err.message}`);
    if (stderr) return res.status(500).send(`Stderr: ${stderr}`);
    res.send(stdout);
  });
});

app.listen(PORT, () => {
  console.log(`Server running at http://localhost:${PORT}`);
});
