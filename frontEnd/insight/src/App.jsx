import { useState } from "react";
import Header from "./Components/Header";
import Feature from "./Components/Feature";
import './App.css';

function App() {
  const [feature, setFeature] = useState();

  const openSelectedFeature = (featureTitle) => {
    if (feature != featureTitle) {
      setFeature(featureTitle);
    }
  };

  return (
    <>
      <Header />
      <h2>Learn Smarter, not harder</h2>

      <div id="features-section">
        <Feature
          title="AI Powered Resource Analyser"
          desc="Analyse your study material for your end goals"
          handleClickSection={openSelectedFeature}
        />

        <Feature
          title="Timers and Techniques"
          desc="Different TImers and Techniques like the pomodoro to boost your productivity"
          handleClickSection={openSelectedFeature}
        />
      </div>
    </>
  );
}

export default App;
