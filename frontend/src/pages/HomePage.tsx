import CallControlPanel from "@/components/CallControlPanel";
import CallDetail from "@/components/CallDetail";

const HomePage = () => {
  return (
    <main className="bg-white flex-1 rounded-[8px] border border-[#E2E8F0] p-[1.125rem] pt-6 space-y-[1.125rem]">
      <CallDetail />
      <CallControlPanel />
    </main>
  );
};

export default HomePage;
