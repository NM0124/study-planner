console.log("UI helpers loaded");

function showCenteredLoader(message = "Loading...") {
  let existing = document.getElementById("__center_loader");
  if (existing) return;
  const el = document.createElement("div");
  el.id = "__center_loader";
  el.style.position = "fixed";
  el.style.left = "0";
  el.style.top = "0";
  el.style.width = "100%";
  el.style.height = "100%";
  el.style.display = "flex";
  el.style.alignItems = "center";
  el.style.justifyContent = "center";
  el.style.zIndex = "9999";
  el.innerHTML = `
    <div style="background: rgba(255,255,255,0.95); padding:20px 26px; border-radius:12px; box-shadow: 0 18px 50px rgba(20,30,60,0.12); text-align:center;">
      <div style="font-size:14px; margin-bottom:8px;">${message}</div>
      <div style="width:36px; height:36px; border-radius:50%; border:4px solid rgba(0,0,0,0.08); border-top-color: rgba(0,0,0,0.24); animation: spin 1s linear infinite;"></div>
    </div>
  `;
  document.body.appendChild(el);
}
function hideCenteredLoader() {
  const el = document.getElementById("__center_loader");
  if (el) el.remove();
}
window.showCenteredLoader = showCenteredLoader;
window.hideCenteredLoader = hideCenteredLoader;

const style = document.createElement('style');
style.innerHTML = `@keyframes spin { from { transform: rotate(0deg) } to { transform: rotate(360deg) } }`;
document.head.appendChild(style);
