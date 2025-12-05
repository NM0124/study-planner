console.log("APP.JS LOADED");

document.addEventListener("DOMContentLoaded", () => {
  const subjectsList = document.getElementById("subjects-list");
  const addBtn = document.getElementById("add-subject-btn");
  const seedBtn = document.getElementById("seed-btn");
  const generateBtn = document.getElementById("generate-btn");
  const rescheduleBtn = document.getElementById("reschedule-btn");
  const saveBtn = document.getElementById("save-btn");
  const exportPdfBtn = document.getElementById("export-pdf-btn");
  const dailyHoursInput = document.getElementById("daily-hours");
  const timetableContainer = document.getElementById("timetable-container");
  const calendarContainer = document.getElementById("calendar-container");
  const unavailablePicker = document.getElementById("unavailable-picker");
  const limitWeekendsCheckbox = document.getElementById("limit-weekends");

  let chart = null;

  function setLatestTimetable(tt) {
    window.latestTimetable = tt;
  }

  function createSubjectRow(data = {}) {
    const div = document.createElement("div");
    div.className = "subject-row";
    div.innerHTML = `
      <input class="s-name" placeholder="Subject" value="${data.name || ''}">
      <label>Size <input class="s-size" type="number" min="1" value="${data.syllabus_size || 1}"></label>
      <label>Difficulty <input class="s-diff" type="number" min="1" max="5" value="${data.difficulty || 3}"></label>
      <label>Importance <input class="s-imp" type="number" min="1" max="5" value="${data.importance || 3}"></label>
      <label>Deadline <input class="s-deadline" type="date" value="${data.deadline || ''}" required></label>
      <label>Type
        <select class="s-type">
          <option ${data.task_type === "Exam" ? "selected" : ""}>Exam</option>
          <option ${data.task_type === "Assignment" ? "selected" : ""}>Assignment</option>
          <option ${data.task_type === "Project" ? "selected" : ""}>Project</option>
        </select>
      </label>
      <button class="remove-sub">X</button>
    `;
    div.querySelector(".remove-sub").onclick = () => div.remove();
    subjectsList.appendChild(div);
  }

  addBtn.onclick = () => createSubjectRow();

  seedBtn.onclick = () => {
    subjectsList.innerHTML = "";
    createSubjectRow({ name: "Mathematics", difficulty: 5, importance:5, syllabus_size:10, deadline: new Date(Date.now()+7*86400e3).toISOString().slice(0,10), task_type:"Exam" });
    createSubjectRow({ name: "DBMS", difficulty: 3, importance:4, syllabus_size:6, deadline: new Date(Date.now()+21*86400e3).toISOString().slice(0,10), task_type:"Assignment" });
    createSubjectRow({ name: "Python", difficulty: 2, importance:3, syllabus_size:4, deadline: new Date(Date.now()+30*86400e3).toISOString().slice(0,10), task_type:"Project" });
  };

  function collectSubjects() {
    const rows = [...document.querySelectorAll(".subject-row")];
    const subjects = [];
    for (const r of rows) {
      const name = r.querySelector(".s-name").value.trim();
      if (!name) continue;
      const deadline = r.querySelector(".s-deadline").value;
      if (!deadline) {
        throw new Error("Deadline required for all subjects");
      }
      subjects.push({
        name,
        syllabus_size: parseFloat(r.querySelector(".s-size").value) || 1,
        difficulty: parseInt(r.querySelector(".s-diff").value) || 3,
        importance: parseInt(r.querySelector(".s-imp").value) || 3,
        deadline,
        task_type: r.querySelector(".s-type").value || "Exam"
      });
    }
    return subjects;
  }

  function renderTimetable(timetable) {
    timetableContainer.innerHTML = "";
    const totals = {}; 
    for (const date of Object.keys(timetable).sort()) {
      const block = document.createElement("div");
      block.className = "day-block";
      block.innerHTML = `<h4>${date}</h4>`;
      const ul = document.createElement("ul");
      if (timetable[date].length === 0) {
        ul.innerHTML = `<li style="color:#777;">Unavailable / No Study</li>`;
      } else {
        for (const slot of timetable[date]) {
          ul.innerHTML += `<li>${slot.subject} — ${slot.hours} hr</li>`;
        }
      }

      block.appendChild(ul);
      timetableContainer.appendChild(block);
    }
    setLatestTimetable(timetable);
    renderChartFromTimetable(timetable);
    renderCalendarHighlights(timetable);
  }

  function renderChartFromTimetable(timetable) {
    const ctx = document.getElementById('chart-distribution').getContext('2d');
    const labels = [];
    const study = [];
    const free = [];
    const dailyLimit = parseFloat(dailyHoursInput.value) || 5;

    Object.keys(timetable).sort().forEach(date=>{
      labels.push(date);
      const hours = timetable[date].reduce((s,x)=>s + (x.hours||0), 0);
      study.push(hours);
      free.push(Math.max(0, dailyLimit - hours));
    });

    if (chart) chart.destroy();
    chart = new Chart(ctx, {
      type: 'bar',
      data: {
        labels,
        datasets: [
          { label: 'Study Hours', data: study },
          { label: 'Free Hours', data: free }
        ]
      },
      options: {
        responsive: true,
        scales: { y: { beginAtZero: true } }
      }
    });
  }

  
  function renderCalendarHighlights(timetable) {
    const sched = {};
    Object.keys(timetable).forEach(d => {
      sched[d] = timetable[d].reduce((a,b)=>a+(b.hours||0),0);
    });

    let unavail = [];
    if (window.flatpickrInstance && window.flatpickrInstance.selectedDates) {
        unavail = window.flatpickrInstance.selectedDates.map(d =>
            d.toISOString().slice(0,10)
        );
    }
    const unavailSet = new Set(unavail);


    calendarContainer.innerHTML = "";
    const now = new Date();
    const y = now.getFullYear(); const m = now.getMonth();
    const first = new Date(y,m,1); const last = new Date(y,m+1,0);
    const table = document.createElement("table"); table.className = "small-calendar";
    const header = document.createElement("tr");
    ["Sun","Mon","Tue","Wed","Thu","Fri","Sat"].forEach(h=>{ const th=document.createElement("th"); th.textContent=h; header.appendChild(th); });
    table.appendChild(header);

    let row = document.createElement("tr");
    for (let blank=0; blank<first.getDay(); blank++) row.appendChild(document.createElement("td"));

    for (let d=1; d<=last.getDate(); d++){
      if (row.children.length === 7) { table.appendChild(row); row = document.createElement("tr"); }
      const cell = document.createElement("td"); cell.textContent = d;
      const iso = new Date(Date.UTC(y, m, d)).toISOString().slice(0,10);
      if (unavailSet.has(iso)) cell.classList.add("cal-unavailable");
      else if (sched[iso] && sched[iso] > 0) {
        const dailyLimit = parseFloat(dailyHoursInput.value) || 5;
        if (sched[iso] >= dailyLimit - 0.01) cell.classList.add("cal-busy");
        else cell.classList.add("cal-partial");
        cell.title = `Scheduled: ${sched[iso]} hr`;
      } else cell.classList.add("cal-free");
      row.appendChild(cell);
    }

    while (row.children.length < 7) row.appendChild(document.createElement("td"));
    table.appendChild(row); calendarContainer.appendChild(table);
  }

  async function exportPDF() {
    if (!window.latestTimetable) { alert("Generate first"); return; }
    const { jsPDF } = window.jspdf;
    const doc = new jsPDF({unit:'pt', format:'a4'});
    const margin = 40;
    let y = 60;
    doc.setFontSize(18);
    doc.text("Study Planner — Timetable", margin, 40);

    doc.setFillColor(40, 100, 200);
    doc.rect(margin, y-10, 520, 24, "F");
    doc.setTextColor(255,255,255);
    doc.setFontSize(12);
    doc.text("Date", margin+6, y+8);
    doc.text("Subject", margin+120, y+8);
    doc.text("Hours", margin+420, y+8);
    y += 26;
    doc.setTextColor(0,0,0);

    for (const date of Object.keys(window.latestTimetable).sort()) {
      doc.setFontSize(12);
      doc.setFont(undefined, "bold");
      doc.text(date, margin+6, y);
      doc.setFont(undefined, "normal");
      y += 16;
      for (const slot of window.latestTimetable[date]) {
        doc.text(slot.subject, margin+120, y);
        doc.text(String(slot.hours), margin+420, y);
        y += 14;
        if (y > 740) { doc.addPage(); y = 60; }
      }
      y += 8;
      if (y > 740) { doc.addPage(); y = 60; }
    }
    doc.save("timetable.pdf");
  }

  async function saveTimetable() {
    if (!window.latestTimetable) { alert("Generate first"); return; }
    const title = prompt("Title for timetable:", "My Timetable");
    try {
      const res = await fetch("/api/save_timetable", {
        method: "POST",
        headers: {"Content-Type":"application/json"},
        body: JSON.stringify({ title, timetable: window.latestTimetable })
      });
      const j = await res.json();
      if (j.status === "ok") alert("Saved (id="+j.timetable_id+")");
      else alert("Save failed");
    } catch (e) {
      alert("Save failed (are you logged in?)");
    }
  }

  async function generate(variant=null) {
    let subjects;
    try { subjects = collectSubjects(); }
    catch (err) { alert(err.message); return; }

    const unavailable_dates = flatpickrInstance
    ? flatpickrInstance.selectedDates.map(d =>
        new Date(Date.UTC(
            d.getFullYear(),
            d.getMonth(),
            d.getDate()
        )).toISOString().slice(0,10)
      )
    : [];

    const payload = {
      subjects,
      daily_hours: parseFloat(dailyHoursInput.value) || 5,
      schedule_type: document.querySelector('input[name="schedule-type"]:checked').value,
      unavailable_dates,
      variant,
      limit_weekends: !!limitWeekendsCheckbox.checked
    };
    try {
      const res = await fetch("/api/generate", {
        method:"POST",
        headers: {"Content-Type":"application/json"},
        body: JSON.stringify(payload)
      });
      const data = await res.json();
      if (data.error) { alert(data.error); return; }
      setLatestTimetable(data.timetable);
      renderTimetable(data.timetable);
    } catch (e) { alert("Generate failed"); }
  }

  async function reschedule() {
  let subjects;
  try { subjects = collectSubjects(); }
  catch (err) { alert(err.message); return; }

  const unavailable_dates = window.flatpickrInstance
    ? window.flatpickrInstance.selectedDates.map(d =>
        new Date(Date.UTC(
            d.getFullYear(),
            d.getMonth(),
            d.getDate()
        )).toISOString().slice(0,10)
      )
    : [];

  const payload = {
    subjects,
    daily_hours: parseFloat(dailyHoursInput.value) || 5,
    schedule_type: document.querySelector('input[name="schedule-type"]:checked').value,
    unavailable_dates,
    limit_weekends: !!limitWeekendsCheckbox.checked
  };

  try {
    const res = await fetch("/api/reschedule", {
      method: "POST",
      headers: {"Content-Type":"application/json"},
      body: JSON.stringify(payload)
    });

    const data = await res.json();

    if (data.error) {
      alert(data.error);
      return;
    }

    renderTimetable(data.timetable);

  } catch (err) {
    alert("Reschedule failed");
  }
}

  const loaded = localStorage.getItem("loaded_timetable");
  if (loaded) {
    const parsed = JSON.parse(loaded);
    if (parsed.timetable) {
      renderTimetable(parsed.timetable);
    }
    localStorage.removeItem("loaded_timetable");
  }

  generateBtn.onclick = () => generate();
  rescheduleBtn.onclick = () => reschedule();
  saveBtn.onclick = () => saveTimetable();
  exportPdfBtn.onclick = () => exportPDF();

  window.flatpickrInstance = flatpickr(unavailablePicker, { mode: "multiple", dateFormat: "Y-m-d" });
  const flatpickrInstance = window.flatpickrInstance;

  createSubjectRow();

});
