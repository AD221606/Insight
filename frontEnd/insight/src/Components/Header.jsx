import { createPortal } from "react-dom";
export default function Header() {
  return createPortal(
    <header>
      <img src="" alt="Insight logo" />
      <h1>Insight</h1>
      <p>Some catchy line</p>
    </header>,
    document.getElementById("body")
  );
}
