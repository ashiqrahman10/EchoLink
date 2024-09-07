import { cn } from "@/lib/utils";
import { DetailedHTMLProps } from "react";

type BoxProps = DetailedHTMLProps<
  React.HTMLAttributes<HTMLDivElement>,
  HTMLDivElement
>;

const Box = ({ className, children, ...props }: BoxProps) => {
  return (
    <div
      className={cn(
        "border rounded-[6px] border-slate-200 bg-white p-6",
        className
      )}
      {...props}
    >
      {children}
    </div>
  );
};

export default Box;
