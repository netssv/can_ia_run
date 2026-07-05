import argparse
import sys
from caniarun import __version__
from caniarun.hardware import detect
from caniarun.compat import evaluate_all
from caniarun.output import format_hw_panel, render_table, render_json, render_analysis_report, render_dashboard

def main():
    parser = argparse.ArgumentParser(description="canirun.ai CLI - AI model compatibility checker")
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    
    subparsers = parser.add_subparsers(dest="command")
    
    # Main scan arguments

    scan_parser = subparsers.add_parser("scan", help="Run hardware scan and model evaluation (default if no subcommand)")
    scan_parser.add_argument("--filter", type=str, help="Filter models by use case")
    scan_parser.add_argument("--family", type=str, help="Filter models by family")
    scan_parser.add_argument("--max-params", type=float, help="Maximum parameters in billions")
    scan_parser.add_argument("--quant", type=str, help="Show only a specific quantization level")
    scan_parser.add_argument("--all-quants", action="store_true", help="Show all quants including F16")
    scan_parser.add_argument("--grade", type=str, choices=["S", "A", "B", "C", "D", "F"], help="Show only models with at least this best grade")
    scan_parser.add_argument("--json", action="store_true", help="Output raw JSON instead of tables")
    scan_parser.add_argument("--hw", action="store_true", help="Show only detected hardware info")
    scan_parser.add_argument("--log", nargs="?", const="caniarun.log", help="Generate a performance log file (defaults to caniarun.log)")
    scan_parser.add_argument("--table", action="store_true", help="Display the full model compatibility table instead of the analyzer report")    
    scan_parser.add_argument("--share-id", type=str, help="Evaluate using a Share ID instead of local hardware")
    
    # Analyze arguments
    analyze_parser = subparsers.add_parser("analyze", help="Analyze a previously generated log file")
    analyze_parser.add_argument("logfile", nargs="?", default="caniarun.log", help="Path to the log file (defaults to caniarun.log)")
    
    # If no subcommand is provided, default to 'scan'
    if len(sys.argv) == 1 or sys.argv[1].startswith("-"):
        args = parser.parse_args(["scan"] + sys.argv[1:])
    else:
        args = parser.parse_args()
        
    if args.command == "analyze":
        import os
        from caniarun.log_analyzer import analyze_log_file
        if not os.path.exists(args.logfile):
            print(f"Error: Log file '{args.logfile}' not found.")
            return 1
            
        report = analyze_log_file(args.logfile)
        
        # Try to extract hardware info from the file for the header
        hw_info = "Unknown Hardware"
        with open(args.logfile, "r") as f:
            for line in f:
                if line.startswith("# Hardware:"):
                    hw_info = line.replace("# Hardware:", "").strip()
                    break
                    
        render_analysis_report(report, args.logfile, hw_info)
        return 0
    
    # ==========================
    # SCAN COMMAND LOGIC
    # ==========================
    
    # 1. Detect hardware
    if args.share_id:
        from caniarun.share import decode_share_id
        try:
            hw = decode_share_id(args.share_id)
        except ValueError as e:
            print(f"Error: {e}")
            return 1
    else:
        hw = detect()
    
    if args.json:
        if args.hw:
            # Just output HW json
            import json
            print(json.dumps({
                "gpu_name": hw.gpu_name,
                "vram_gb": hw.vram_gb,
                "system_ram_gb": hw.system_ram_gb,
                "memory_bandwidth": hw.memory_bandwidth,
                "platform": hw.platform,
                "is_apple_silicon": hw.is_apple_silicon
            }, indent=2))
            return 0
    else:
        if args.hw:
            format_hw_panel(hw)
            return 0
            
    # 2. Evaluate models
    results = evaluate_all(hw)
    
    # 3. Apply filters
    if args.filter:
        use_case = args.filter.lower()
        results = [r for r in results if any(use_case in u.lower() for u in r.model.use_case)]
        
    if args.family:
        family = args.family.lower()
        results = [r for r in results if family in r.model.family.lower()]
        
    if args.max_params is not None:
        results = [r for r in results if r.model.params_billions <= args.max_params]
        
    if args.grade:
        grade_vals = {"S": 6, "A": 5, "B": 4, "C": 3, "D": 2, "F": 1}
        min_val = grade_vals[args.grade.upper()]
        results = [r for r in results if grade_vals.get(r.best_grade, 0) >= min_val]
        
    # Emit log if requested (before table rendering)
    if args.log:
        from caniarun.log_emitter import emit_log
        emit_log(hw, results, args.log, args.all_quants)
        if not args.json:
            print(f"Log generated successfully at {args.log}\n")
        
    # 4. Output
    if args.json:
        render_json(hw, results)
    elif args.table:
        format_hw_panel(hw)
        render_table(results, show_f16=args.all_quants, specific_quant=args.quant)
    else:
        # Default user-friendly behavior: Run Textual TUI
        if sys.stdin.isatty():
            from caniarun.tui.app import CaniarunApp
            app = CaniarunApp(hw=hw, results=results)
            app.run()
        else:
            # Fallback for non-interactive shells
            render_dashboard(hw, results)
        
    return 0

if __name__ == "__main__":
    sys.exit(main())
