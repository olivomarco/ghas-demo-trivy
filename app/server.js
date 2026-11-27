const express = require('express');
const _ = require('lodash');

const app = express();
const port = process.env.PORT || 3000;

app.get('/', (req, res) => {
  res.json({ message: 'Hello from the GHAS + Trivy demo!' });
});

app.get('/healthz', (req, res) => {
  res.json({ status: 'ok' });
});

app.get('/merge', (req, res) => {
  res.json(_.merge({}, { app: 'trivy-demo' }, req.query));
});

app.listen(port, () => {
  console.log(`Demo app listening on port ${port}`);
});
