"""
MCP Server - Model Context Protocol integration for LLM interaction
"""

import os
import json
from typing import Any, Dict, List
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

from .task_manager import TaskManager
from .search import TaskSearcher


# Initialize server
app = Server("taskmaster")

# Initialize managers
tasks_dir = os.environ.get('TASKMASTER_TASKS_DIR', './tasks')
task_manager = TaskManager(tasks_dir)
task_searcher = TaskSearcher(tasks_dir)


@app.list_tools()
async def list_tools() -> List[Tool]:
    """List available tools for the LLM"""
    return [
        Tool(
            name="create_task",
            description="Create a new task card in markdown format. Path MUST include a project folder (e.g., 'project1/task1.md', not 'task1.md').",
            inputSchema={
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Relative path for the task (e.g., 'project1/task1.md'). MUST include a project folder as the top-level directory."
                    },
                    "title": {
                        "type": "string",
                        "description": "Task title"
                    },
                    "content": {
                        "type": "string",
                        "description": "Task content in markdown"
                    },
                    "status": {
                        "type": "string",
                        "description": "Task status (open, in-progress, done, etc.)",
                        "default": "open"
                    },
                    "priority": {
                        "type": "string",
                        "description": "Task priority (low, medium, high, critical)",
                        "default": "medium"
                    },
                    "tags": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of tags"
                    }
                },
                "required": ["path", "title"]
            }
        ),
        Tool(
            name="read_task",
            description="Read a task card by its path. Path MUST include a project folder.",
            inputSchema={
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Relative path to the task. MUST include a project folder (e.g., 'project1/task1.md')."
                    }
                },
                "required": ["path"]
            }
        ),
        Tool(
            name="update_task",
            description="Update an existing task card. Path MUST include a project folder.",
            inputSchema={
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Relative path to the task. MUST include a project folder (e.g., 'project1/task1.md')."
                    },
                    "title": {
                        "type": "string",
                        "description": "New title (optional)"
                    },
                    "content": {
                        "type": "string",
                        "description": "New content (optional)"
                    },
                    "metadata": {
                        "type": "object",
                        "description": "Metadata to update (merged with existing)"
                    }
                },
                "required": ["path"]
            }
        ),
        Tool(
            name="delete_task",
            description="Delete a task card. Path MUST include a project folder.",
            inputSchema={
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Relative path to the task. MUST include a project folder (e.g., 'project1/task1.md')."
                    }
                },
                "required": ["path"]
            }
        ),
        Tool(
            name="list_tasks",
            description="List tasks in a directory (token-efficient summary)",
            inputSchema={
                "type": "object",
                "properties": {
                    "subpath": {
                        "type": "string",
                        "description": "Subdirectory to list (empty for all)",
                        "default": ""
                    },
                    "recursive": {
                        "type": "boolean",
                        "description": "Include subdirectories",
                        "default": True
                    }
                },
                "required": []
            }
        ),
        Tool(
            name="search_tasks",
            description="Search tasks with text and metadata filters (token-efficient)",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Text to search in title and content"
                    },
                    "status": {
                        "type": "string",
                        "description": "Filter by status"
                    },
                    "priority": {
                        "type": "string",
                        "description": "Filter by priority"
                    },
                    "tags": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Filter by tags"
                    },
                    "path_pattern": {
                        "type": "string",
                        "description": "Path pattern to search (e.g., 'project1/**')"
                    },
                    "max_results": {
                        "type": "integer",
                        "description": "Maximum results to return",
                        "default": 20
                    }
                },
                "required": []
            }
        ),
        Tool(
            name="get_structure",
            description="Get hierarchical folder structure (token-efficient overview)",
            inputSchema={
                "type": "object",
                "properties": {
                    "subpath": {
                        "type": "string",
                        "description": "Subdirectory to show structure for",
                        "default": ""
                    }
                },
                "required": []
            }
        ),
        Tool(
            name="move_task",
            description="Move or rename a task. Both paths MUST include a project folder.",
            inputSchema={
                "type": "object",
                "properties": {
                    "old_path": {
                        "type": "string",
                        "description": "Current path. MUST include a project folder (e.g., 'project1/task1.md')."
                    },
                    "new_path": {
                        "type": "string",
                        "description": "New path. MUST include a project folder (e.g., 'project1/newtask.md')."
                    }
                },
                "required": ["old_path", "new_path"]
            }
        ),
        Tool(
            name="get_all_tags",
            description="Get all unique tags across all tasks",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        )
    ]


@app.call_tool()
async def call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
    """Handle tool calls from the LLM"""
    
    try:
        if name == "create_task":
            metadata = {}
            if 'status' in arguments:
                metadata['status'] = arguments['status']
            if 'priority' in arguments:
                metadata['priority'] = arguments['priority']
            if 'tags' in arguments:
                metadata['tags'] = arguments['tags']
            
            result = task_manager.create_task(
                path=arguments['path'],
                title=arguments['title'],
                content=arguments.get('content', ''),
                metadata=metadata if metadata else None
            )
            
            return [TextContent(
                type="text",
                text=f"✓ Created task '{result['title']}' at {result['path']}"
            )]
        
        elif name == "read_task":
            task = task_manager.read_task(arguments['path'])
            if not task:
                return [TextContent(
                    type="text",
                    text=f"✗ Task not found: {arguments['path']}"
                )]
            
            # Format task info in a token-efficient way
            output = f"**{task['title']}**\n\n"
            output += f"Path: {task['path']}\n\n"
            
            # Key metadata
            for key in ['status', 'priority', 'tags', 'created', 'updated']:
                if key in task['metadata']:
                    output += f"{key.title()}: {task['metadata'][key]}\n"
            
            output += f"\n---\n\n{task['content']}"
            
            return [TextContent(type="text", text=output)]
        
        elif name == "update_task":
            result = task_manager.update_task(
                path=arguments['path'],
                title=arguments.get('title'),
                content=arguments.get('content'),
                metadata=arguments.get('metadata')
            )
            
            if not result:
                return [TextContent(
                    type="text",
                    text=f"✗ Task not found: {arguments['path']}"
                )]
            
            return [TextContent(
                type="text",
                text=f"✓ Updated task: {result['path']}"
            )]
        
        elif name == "delete_task":
            success = task_manager.delete_task(arguments['path'])
            
            return [TextContent(
                type="text",
                text=f"✓ Deleted task: {arguments['path']}" if success 
                     else f"✗ Task not found: {arguments['path']}"
            )]
        
        elif name == "list_tasks":
            tasks = task_manager.list_tasks(
                subpath=arguments.get('subpath', ''),
                recursive=arguments.get('recursive', True),
                include_content=False
            )
            
            if not tasks:
                return [TextContent(type="text", text="No tasks found.")]
            
            # Token-efficient summary
            output = f"Found {len(tasks)} tasks:\n\n"
            for task in tasks:
                status = task['metadata'].get('status', 'unknown')
                priority = task['metadata'].get('priority', '-')
                output += f"• [{status}] {task['title']}\n  Path: {task['path']} | Priority: {priority}\n"
            
            return [TextContent(type="text", text=output)]
        
        elif name == "search_tasks":
            metadata_filters = {}
            if 'status' in arguments:
                metadata_filters['status'] = arguments['status']
            if 'priority' in arguments:
                metadata_filters['priority'] = arguments['priority']
            if 'tags' in arguments:
                metadata_filters['tags'] = arguments['tags']
            
            results = task_searcher.search(
                query=arguments.get('query', ''),
                metadata_filters=metadata_filters if metadata_filters else None,
                path_pattern=arguments.get('path_pattern', ''),
                max_results=arguments.get('max_results', 20),
                include_content=False
            )
            
            if not results:
                return [TextContent(type="text", text="No tasks found.")]
            
            # Token-efficient results
            output = f"Found {len(results)} matching tasks:\n\n"
            for r in results:
                output += f"• {r['title']} (relevance: {r['score']})\n"
                output += f"  Path: {r['path']}\n"
                if 'snippet' in r:
                    output += f"  Snippet: {r['snippet'][:100]}...\n"
                output += "\n"
            
            return [TextContent(type="text", text=output)]
        
        elif name == "get_structure":
            structure = task_manager.get_structure(arguments.get('subpath', ''))
            
            def format_tree(node, indent=0):
                result = "  " * indent + f"📁 {node['name']}\n" if node['type'] == 'directory' else ""
                
                if node['type'] == 'directory' and 'children' in node:
                    for child in node['children']:
                        if child['type'] == 'directory':
                            result += format_tree(child, indent + 1)
                        else:
                            status = child.get('metadata', {}).get('status', '?')
                            result += "  " * (indent + 1) + f"📄 {child['title']} [{status}]\n"
                
                return result
            
            output = format_tree(structure)
            return [TextContent(type="text", text=output or "Empty structure")]
        
        elif name == "move_task":
            success = task_manager.move_task(
                arguments['old_path'],
                arguments['new_path']
            )
            
            return [TextContent(
                type="text",
                text=f"✓ Moved task" if success else "✗ Failed to move task"
            )]
        
        elif name == "get_all_tags":
            tags = task_searcher.get_all_tags()
            
            if not tags:
                return [TextContent(type="text", text="No tags found.")]
            
            output = "Tags: " + ", ".join(sorted(tags))
            return [TextContent(type="text", text=output)]
        
        else:
            return [TextContent(
                type="text",
                text=f"Unknown tool: {name}"
            )]
    
    except Exception as e:
        return [TextContent(
            type="text",
            text=f"Error executing {name}: {str(e)}"
        )]


async def run_server():
    """Run the MCP server"""
    async with stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, app.create_initialization_options())


def main():
    """Main entry point for MCP server"""
    import asyncio
    asyncio.run(run_server())


if __name__ == '__main__':
    main()
