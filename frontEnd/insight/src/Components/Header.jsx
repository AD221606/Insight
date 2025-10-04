import "./Header.css";
import InsightLogo from "../assets/eye-6-svgrepo-com.svg";

export default function Header() {
  return (
    <a href="#header">
      <header id="header">
        <img src={InsightLogo} alt="Insight logo" />
        <h1>Insight</h1>
      </header>
    </a>
  );
}
