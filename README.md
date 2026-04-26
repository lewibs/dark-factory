██████╗  █████╗ ██████╗ ██╗  ██╗
██╔══██╗██╔══██╗██╔══██╗██║ ██╔╝
██║  ██║███████║██████╔╝█████╔╝ 
██║  ██║██╔══██║██╔══██╗██╔═██╗ 
██████╔╝██║  ██║██║  ██║██║  ██╗
╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═╝╚═╝  ╚═╝
███████╗ █████╗  ██████╗████████╗ ██████╗ ██████╗ ██╗   ██╗
██╔════╝██╔══██╗██╔════╝╚══██╔══╝██╔═══██╗██╔══██╗╚██╗ ██╔╝
█████╗  ███████║██║        ██║   ██║   ██║██████╔╝ ╚████╔╝ 
██╔══╝  ██╔══██║██║        ██║   ██║   ██║██╔══██╗  ╚██╔╝  
██║     ██║  ██║╚██████╗   ██║   ╚██████╔╝██║  ██║   ██║   
╚═╝     ╚═╝  ╚═╝ ╚═════╝   ╚═╝    ╚═════╝ ╚═╝  ╚═╝   ╚═╝  
Dark Factory is a fully autonomous coding plugin for Claude Code. One command. No hand-holding. Done.

Build features	Designs, implements, reviews, and ships new functionality end-to-end
Fix bugs	Diagnoses failures, applies fixes, and verifies — without you touching the code
Repair broken flows	Detects broken integrations, loops through fixes, and restores green CI
All three run 100% autonomously — Dark Factory handles planning, implementation, code review, PR, and cleanup from start to finish.

Install
git clone https://github.com/lewibs/dark-factory
cd dark-factory
claude plugin marketplace add "$(pwd)"
claude plugin install dark-factory
Verify
claude plugin list
Commands
Command	Input	Description
/dark-factory:manufacture	Task description (e.g. "add OAuth login")	Full orchestration — routes to the right agent (feature, debug, or fix-flow) end-to-end, runs code review, opens a PR, and cleans up
/dark-factory:init	Optional GitHub URL	Onboard a project onto dark factory — sets up the structure for infinite autonomous changes and generates a CLAUDE.md
/dark-factory:update	None	Update the plugin to the latest version
