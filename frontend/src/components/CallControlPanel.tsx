import {
  Lightbulb,
  Mail,
  MicOff,
  Pause,
  PhoneCall,
  Settings,
} from "lucide-react";
import Box from "./ui/Box";
import { Button } from "./ui/button";

const CallControlPanel = () => {
  return (
    <Box className="flex justify-between items-center">
      <div className="space-x-2.5">
        <Button className="gap-2" variant="outline">
          <Pause className="text-[#111111] w-4 h-4" />
          <span className="font-medium text-[#111]">Hold</span>
        </Button>
        <Button className="gap-2" variant="outline">
          <MicOff className="text-[#111111] w-4 h-4" />
          <span className="font-medium text-[#111]">Mute</span>
        </Button>
        <Button className="gap-2" variant="outline">
          <Mail className="text-[#111111] w-4 h-4" />
          <span className="font-medium text-[#111]">Message</span>
        </Button>
        <Button className="gap-2" variant="outline">
          <Lightbulb className="text-[#111111] w-4 h-4" />
          <span className="font-medium text-[#111]">Transcribe</span>
        </Button>
        <Button className="gap-2" variant="outline">
          <Settings className="text-[#111111] w-4 h-4" />
          <span className="font-medium text-[#111]">Settings</span>
        </Button>
      </div>
      <div>
        <Button className="gap-2 bg-[#A2191F]" variant="destructive">
          <PhoneCall className="w-4 h-4" />
          <span className="font-medium">End Call</span>
        </Button>
      </div>
    </Box>
  );
};

export default CallControlPanel;
