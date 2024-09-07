import { Link, useLocation } from "react-router-dom";
import EchoLinkLogo from "@/assets/echo-link-logo.svg";
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  // Calculator,
  // Calendar,
  // CreditCard,
  // Settings,
  SettingsIcon,
  // Smile,
  // User,
} from "lucide-react";

import {
  Command,
  // CommandEmpty,
  // CommandGroup,
  CommandInput,
  // CommandItem,
  // CommandList,
  // CommandSeparator,
  // CommandShortcut,
} from "@/components/ui/command";
import { Button } from "./ui/button";
import { Avatar, AvatarFallback, AvatarImage } from "./ui/avatar";

const links = [
  { label: "Dashboard", link: "/" },
  { label: "Call history", link: "/call-history" },
  { label: "Analytics", link: "/analytics" },
  { label: "Dispatch", link: "/dispatch" },
];

const Navbar = () => {
  const location = useLocation();
  return (
    <header className="shrink-0 flex items-center gap-[2.875rem] py-[1.125rem] px-3.5">
      <div>
        <Link
          to="/"
          className="text-2xl font-bold inline-flex gap-[1.125rem] items-center justify-center"
        >
          <img className="w-6 h-6" src={EchoLinkLogo} alt="logo" />
          <h1 className="font-[300] font-poppins">
            Echo<span className="font-medium">Link</span>
          </h1>
        </Link>
      </div>
      <div>
        <Tabs value={location.pathname} className="w-[400px]">
          <TabsList className="">
            {links.map((link) => (
              <TabsTrigger asChild key={link.link} value={link.link}>
                <Link to={link.link}>{link.label}</Link>
              </TabsTrigger>
            ))}
          </TabsList>
        </Tabs>
      </div>
      <div className="flex-1">
        <CommandDemo />
      </div>
      <div className="flex gap-3">
        <Button variant="ghost">
          <SettingsIcon className="text-slate-800" />
        </Button>
        <Avatar>
          <AvatarImage src="https://github.com/shadcn.png" />
          <AvatarFallback>CN</AvatarFallback>
        </Avatar>
      </div>
    </header>
  );
};

export function CommandDemo() {
  return (
    <Command className="rounded-lg border shadow-md md:min-w-[450px] w-full">
      <CommandInput placeholder="Type a command or search..." />
      {/* <CommandList>
        <CommandEmpty>No results found.</CommandEmpty>
        <CommandGroup heading="Suggestions">
          <CommandItem>
            <Calendar className="mr-2 h-4 w-4" />
            <span>Calendar</span>
          </CommandItem>
          <CommandItem>
            <Smile className="mr-2 h-4 w-4" />
            <span>Search Emoji</span>
          </CommandItem>
          <CommandItem disabled>
            <Calculator className="mr-2 h-4 w-4" />
            <span>Calculator</span>
          </CommandItem>
        </CommandGroup>
        <CommandSeparator />
        <CommandGroup heading="Settings">
          <CommandItem>
            <User className="mr-2 h-4 w-4" />
            <span>Profile</span>
            <CommandShortcut>⌘P</CommandShortcut>
          </CommandItem>
          <CommandItem>
            <CreditCard className="mr-2 h-4 w-4" />
            <span>Billing</span>
            <CommandShortcut>⌘B</CommandShortcut>
          </CommandItem>
          <CommandItem>
            <Settings className="mr-2 h-4 w-4" />
            <span>Settings</span>
            <CommandShortcut>⌘S</CommandShortcut>
          </CommandItem>
        </CommandGroup>
      </CommandList> */}
    </Command>
  );
}

export default Navbar;
