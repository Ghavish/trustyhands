// "Add New Project" button of the Portfolio Hub.
// Copies the empty project form and gives it the next number.

document.addEventListener("DOMContentLoaded", () => {
  const list = document.getElementById("project-list");
  const template = document.getElementById("project-template");
  const total = document.getElementById("id_projects-TOTAL_FORMS");
  const counter = document.getElementById("project-count");

  document.getElementById("add-project").addEventListener("click", () => {
    const index = Number(total.value);
    const html = template.innerHTML.replace(/__prefix__/g, String(index));
    list.insertAdjacentHTML("beforeend", html);
    total.value = index + 1;
    counter.textContent = index + 1;
    list.scrollTop = list.scrollHeight;
  });

  // Show the chosen file name under each upload button.
  list.addEventListener("change", (event) => {
    const input = event.target;
    if (input.type !== "file") return;
    const text = input.closest(".ob-upload").querySelector("span");
    const count = input.files.length;
    if (count === 1) text.textContent = input.files[0].name;
    if (count > 1) text.textContent = count + " files";
  });
});
