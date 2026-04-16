import { BrowserRouter, Routes, Route } from "react-router-dom";
import { Nav } from "./components/Nav";
import { Advisor } from "./pages/Advisor";
import { Schedule } from "./pages/Schedule";

export default function App() {
  return (
    <BrowserRouter>
      <div className="min-h-screen bg-pawpal-bg">
        <Nav />
        <Routes>
          <Route path="/" element={<Advisor />} />
          <Route path="/schedule" element={<Schedule />} />
        </Routes>
      </div>
    </BrowserRouter>
  );
}
