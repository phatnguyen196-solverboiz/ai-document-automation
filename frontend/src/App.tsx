import { BrowserRouter, Route, Routes } from "react-router-dom";
import { Layout } from "./components/Layout";
import { DashboardPage } from "./pages/DashboardPage";
import { DocumentPage } from "./pages/DocumentPage";
import { ResultPage } from "./pages/ResultPage";
import { ReviewPage } from "./pages/ReviewPage";
import { UploadPage } from "./pages/UploadPage";

export default function App() {
  return <BrowserRouter><Routes><Route element={<Layout />}><Route index element={<DashboardPage />} /><Route path="upload" element={<UploadPage />} /><Route path="documents/:id" element={<DocumentPage />} /><Route path="documents/:id/review" element={<ReviewPage />} /><Route path="documents/:id/result" element={<ResultPage />} /></Route></Routes></BrowserRouter>;
}
