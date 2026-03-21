const button = document.getElementById("ping");
const output = document.getElementById("output");

button?.addEventListener("click", () => {
  const timestamp = new Date().toISOString();
  output.textContent = `UI ready at ${timestamp}`;
});
