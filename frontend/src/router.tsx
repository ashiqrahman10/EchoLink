import { createBrowserRouter } from "react-router-dom";
import HomePage from "./pages/HomePage";
import Layout from "./components/Layout";

const router = createBrowserRouter([
  {
    path: "/",
    Component: Layout,
    children: [
      {
        index: true,
        Component: HomePage,
      },
      {
        path: "/call-history",
        Component: () => <div>Call history</div>,
      },
      {
        path: "/analytics",
        Component: () => <div>Analytics</div>,
      },
      {
        path: "/dispatch",
        Component: () => <div>Dispatch</div>,
      },
    ],
  },
]);

export default router;
