import { Disc } from "lucide-react";
import Box from "@/components/ui/Box";
import { Button } from "@/components/ui/button";
import profilePhoto from "@/assets/photo.png";

const CallDetail = () => {
  return (
    <div className="grid grid-cols-2 gap-[1.125rem]">
      <Box className="space-y-4">
        <div className="flex items-center gap-2.5">
          <Button variant="outline">+91 91882 70912</Button>
          <Button className="gap-2" variant="destructive">
            <Disc className="w-4 h-4" />
            <span>Rec</span>
          </Button>
        </div>
        <h2 className="font-medium text-[1.375rem] leading-[109%] text-[#111]">
          Bradley Cooper
        </h2>
        <div className="flex gap-3 font-medium">
          <img src={profilePhoto} alt="profile photo" />
          <div>
            <p className="text-sm">Location:</p>
            <p className="max-w-[175px] text-[0.75rem] leading-[normal]">
              21st, First Floor, UKC Road, TX, USA - 43782
            </p>
          </div>
        </div>
      </Box>
      <Box className="grid grid-cols-2">
        <div>
          <h3>Transcription</h3>
          <hr />
          <div>
            <p>Hello how are you,</p>
            <p>I am fine</p>
            <p>I am fine</p>
            <p>I am fine</p>
            <p>I am fine</p>
          </div>
        </div>
        <div>
          <h3>EchoAnalysis</h3>
            <hr />
            <div>
              <p>Analysis of the call</p>
              
        </div>
      </Box>
    </div>
  );
};

export default CallDetail;
