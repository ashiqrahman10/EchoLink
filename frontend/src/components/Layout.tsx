import { Outlet } from "react-router-dom";
import Navbar from "./Navbar";

const Layout = () => {
  return (
    <div className="bg-[#F7F7F7] h-screen px-[1.125rem] pb-[1.125rem] flex flex-col">
      <Navbar />
      <Outlet />
    </div>
  );
};

export default Layout;
