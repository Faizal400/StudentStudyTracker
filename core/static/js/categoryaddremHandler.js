// --- CSRF helper (required for Django POST requests) ---
function getCookie(name) {
  const cookies = document.cookie ? document.cookie.split(";") : [];
  for (let c of cookies) {
    c = c.trim();
    if (c.startsWith(name + "=")) {
      return decodeURIComponent(c.substring(name.length + 1));
    }
  }
  return null;
}

const csrftoken = getCookie("csrftoken");

const subjectsList = document.getElementById("subjectsList");
const removeSelect = document.getElementById("removeSubjectSelect");

const chooseModalEl = document.getElementById("chooseCategoryModal");

const options = document.querySelectorAll('#chooseCategoryModal a[data-type]');
const subjectOption = document.querySelector('#chooseCategoryModal a[data-type="subject"]');
const moduleOption = document.querySelector('#chooseCategoryModal a[data-type="module"]');
const submoduleOption = document.querySelector('#chooseCategoryModal a[data-type="submodule"]');
let selectedType = null;

const confirmOptionSelection = document.getElementById("confirmCategorySelection");
const cancelOptionSelection = document.getElementById("cancelCategorySelection");

const confirmAddMSM = document.getElementById("confirmAddMSM");
const msmError = document.getElementById("msmError");
const msmNameInput = document.getElementById("msmNameInput");
const subjectSelect = document.getElementById("subjectSelect");
const moduleSelect = document.getElementById("moduleSelect");

const subjectNameInput = document.getElementById("subjectNameInput");
const confirmAddSubject = document.getElementById("confirmAddSubject");
const addSubjectError = document.getElementById("addSubjectError");

const confirmRemoveSubject = document.getElementById("confirmRemoveSubject");
const removeSubjectError = document.getElementById("removeSubjectError");

const confirmRemoveMSM = document.getElementById("confirmRemoveMSM");
const removeMSMError = document.getElementById("msmremError");
const selectedModuleRemove = document.getElementById("remMselect");
const selectedSubModuleRemove = document.getElementById("remSMselect");



let AddorRemove = "";

window.$('#chooseCategoryModal').on('show.bs.modal', function (e) {
  console.log("Modal is opening");
  var chooseCategoryTitle = document.querySelector('#chooseCategoryModal .modal-title');
  const trigger = e.relatedTarget;   // the button that opened it
  console.log("Trigger:", trigger);

  if (trigger) {
    action = trigger.dataset.action
    console.log("data-action:", action);
    console.log("Action:", action);
    AddorRemove = action;
    if (action == "add") {
      confirmOptionSelection.classList.remove("btn-warning");
      confirmOptionSelection.classList.add("btn-success");
      chooseCategoryTitle.textContent = "Which category do you want to create?";
      //confirmOptionSelection.textContent = "Add";
    } else if (action == "remove") {
      confirmOptionSelection.classList.remove("btn-success");
      confirmOptionSelection.classList.add("btn-warning");
      chooseCategoryTitle.textContent = "Which category do you want to remove?";
      //confirmOptionSelection.textContent = "Remove";

    }
  }
});

// Click Handler for add category modal

options.forEach(option => {
  option.addEventListener("click", (e) => {
    e.preventDefault(); // stop page from jumping to top

    // remove active from all
    options.forEach(el => el.classList.remove("active"));

    // add active to the clicked one
    option.classList.add("active");

    // remember which type was picked
    selectedType = option.dataset.type;
    console.log("Selected:", selectedType);
  });
});
cancelOptionSelection.addEventListener("click", (e) => {
  // remove active from all
  options.forEach(el => el.classList.remove("active"));
  selectedType = null;
});

// Confirm category selection
confirmOptionSelection.addEventListener("click", (e) => {
  if (selectedType == "subject") {
    window.$("#chooseCategoryModal").modal("hide");
    if (AddorRemove == "add") {
      window.$("#addSubjectModal").modal("show");
    } else if (AddorRemove == "remove") {
      window.$("#removeSubjectModal").modal("show");
    }
  } else if (selectedType == "module" || selectedType == "submodule") {
    window.$("#chooseCategoryModal").modal("hide");
    if (AddorRemove == "add") {
      var MSMTitle = document.querySelector('#addModuleSubModuleModal .modal-title');
      MSMTitle.textContent = "".concat("Add a ", selectedType);
      if (selectedType == "module") {
        moduleSelect.style.display = "none";
        subjectSelect.style.display = ""; //or block 2show
      } else {
        subjectSelect.style.display = "none";
        moduleSelect.style.display = ""; // or block to show
      }
      window.$("#addModuleSubModuleModal").modal("show");
    } else if (AddorRemove == "remove") {
      var MSMTitle = document.querySelector('#removeModuleSubModuleModal .modal-title');
      remModuleSelect = document.getElementById("remMselect");
      remSubModuleSelect = document.getElementById("remSMselect");
      if (selectedType == "module") {
        MSMTitle.textContent = "Select a " + selectedType + " to remove";
        remSubModuleSelect.style.display = "none";
        remModuleSelect.style.display = ""; //or block 2show
      } else {
        MSMTitle.textContent = "Select a " + selectedType + " to remove";
        remModuleSelect.style.display = "none";
        remSubModuleSelect.style.display = ""; // or block to show
      }
      window.$("#removeModuleSubModuleModal").modal("show");
    }

  } else {
    console.log(selectedType);
  }
  // remove active from all
  options.forEach(el => el.classList.remove("active"));
  //selectedType = null;
});
// Remove "No subjects yet." message if present
function removeEmptyMsgIfExists() {
  const msg = document.getElementById("noSubjectsMsg");
  if (msg) msg.remove();
}

// Add subject to DOM list + remove dropdown
function addSubjectToUI(subject) {
  removeEmptyMsgIfExists();

  const li = document.createElement("li");
  li.dataset.subjectId = subject.id;
  li.textContent = subject.name;
  subjectsList.appendChild(li);

  const opt = document.createElement("option");
  opt.value = subject.id;
  opt.textContent = subject.name;
  removeSelect.appendChild(opt);
}

// Remove subject from DOM list + remove dropdown
function removeSubjectFromUI(subjectId) {
  const li = subjectsList.querySelector(`li[data-subject-id="${subjectId}"]`);
  if (li) li.remove();

  const opt = removeSelect.querySelector(`option[value="${subjectId}"]`);
  if (opt) opt.remove();

  // If list becomes empty, show message
  if (subjectsList.querySelectorAll("li").length === 0) {
    const emptyLi = document.createElement("li");
    emptyLi.id = "noSubjectsMsg";
    emptyLi.textContent = "No subjects yet.";
    subjectsList.appendChild(emptyLi);
  }
}

// --- Add subject to database (AJAX) ---
confirmAddSubject.addEventListener("click", async () => {
  addSubjectError.textContent = "";

  const name = (subjectNameInput.value || "").trim();
  const dataType = "subject";
  if (!name) {
    addSubjectError.textContent = "Please enter a subject name.";
    return;
  }

  try {
    const res = await fetch("/api/subjects/add/", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-CSRFToken": csrftoken,
      },
      body: JSON.stringify({ name: name, dataType: dataType, ParentId: "none" })
    });

    const data = await res.json();

    if (!data.ok) {
      addSubjectError.textContent = data.error || "Failed to add subject.";
      return;
    }

    addSubjectToUI(data.subject);
    subjectNameInput.value = "";

    // Close modal (Bootstrap 4)
    window.$("#addSubjectModal").modal("hide");
    location.reload(); // Reload the page to reflect changes (simplest way)
  } catch (err) {
    addSubjectError.textContent = "Network error. Check your server is running.";
  }
});


// --- Add module/sub module to database (AJAX) ---
confirmAddMSM.addEventListener("click", async () => {
  msmError.textContent = "";
  const name = (msmNameInput.value || "").trim();
  if (!name) {
    msmError.textContent = "Please enter a " + selectedType + " name.";
    return;
  }
  selectedParentId = null;
  console.log("Type: " + selectedType)
  if (selectedType == "module") {
    selectedParentId = subjectSelect.value
  } else if (selectedType == "submodule") {
    selectedParentId = moduleSelect.value
  }
  try {
    const res = await fetch("/api/subjects/add/", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-CSRFToken": csrftoken,
      },
      body: JSON.stringify({ name: name, dataType: selectedType, ParentId: selectedParentId })
    });

    const data = await res.json();

    if (!data.ok) {
      msmError.textContent = data.error || "Failed to add " + selectedType + ".";
      return;
    }


    //addSubjectToUI(data.subject);
    msmNameInput.value = "";

    // Close modal (Bootstrap 4)
    selectedType = null;
    window.$("#addModuleSubModuleModal").modal("hide");
    location.reload(); // Reload the page to reflect changes (simplest way)
  } catch (err) {
    msmError.textContent = "Network error. Check your server is running.";
  }
});

// --- Remove subject (AJAX) ---
confirmRemoveSubject.addEventListener("click", async () => {
  removeSubjectError.textContent = "";

  const id = removeSelect.value;
  if (!id) {
    removeSubjectError.textContent = "No subjects to remove.";
    return;
  }

  try {
    const res = await fetch("/api/subjects/delete/", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-CSRFToken": csrftoken,
      },
      body: JSON.stringify({ id: id, type: selectedType }),
    });

    const data = await res.json();

    if (!data.ok) {
      removeMSMError.textContent = data.error || "Failed to remove module/submodule.";
      return;
    }

    removeSubjectFromUI(data.deleted_id);
    console.log("Removed type:", selectedType);
    // Close modal
    window.$("#removeSubjectModal").modal("hide");
    location.reload(); // Reload the page to reflect changes (simplest way)
  } catch (err) {
    removeSubjectError.textContent = "Network error. Check your server is running.";

  }
});

// --- Remove Modules/SubModules (AJAX) ---
confirmRemoveMSM.addEventListener("click", async () => {
  console.log("Attempting to remove type:", selectedType);
  removeMSMError.textContent = "";
  var optionID = null;
  if (selectedType == "module") {
    console.log("Selected module ID to remove:", selectedModuleRemove.value);
    optionID = selectedModuleRemove.value;
  } else if (selectedType == "submodule") {
    console.log("Selected submodule ID to remove:", selectedSubModuleRemove.value);
    optionID = selectedSubModuleRemove.value;
  };
  if (!optionID) {
    console.log("No option selected for removal.");
    removeMSMError.textContent = "No modules/submodules to remove.";
    return;
  }
  try {
    const res = await fetch("/api/subjects/delete/", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-CSRFToken": csrftoken,
      },
      body: JSON.stringify({ id: optionID, type: selectedType }),
    });
    const data = await res.json();

    if (!data.ok) {
      removeMSMError.textContent = data.error || "Failed to remove module/submodule.";
      return;
    }
    
    //removeSubjectFromUI(data.deleted_id);
    console.log("Removed type:", selectedType);
    // Close modal
    selectedType = null;
    window.$("#removeModuleSubModuleModal").modal("hide");
    console.log("Closed remove modal. Successfully sent!");
    location.reload(); // Reload the page to reflect changes (simplest way)
  } catch (err) {
    removeMSMError.textContent = "Network error. Check your server is running.";
    console.error("Error during removal:", err);
  }
});