# framework/github_utils.py
import re
import json
from typing import List, Dict, Any
from langchain_core.messages import BaseMessage, AIMessage

def extract_github_links_from_messages(messages: List[BaseMessage]) -> List[str]:
    """Extract GitHub URLs from LLM messages that contain tool call results."""
    github_links = []
    
    for message in messages:
        if isinstance(message, AIMessage):
            # Check if the message has tool calls
            if hasattr(message, 'tool_calls') and message.tool_calls:
                for tool_call in message.tool_calls:
                    # Extract links from tool call arguments if they contain GitHub URLs
                    if hasattr(tool_call, 'args') and tool_call.args:
                        links = _extract_links_from_data(tool_call.args)
                        github_links.extend(links)
            
            # Extract links from the message content
            if message.content:
                content_links = _extract_github_urls_from_text(message.content)
                github_links.extend(content_links)
                
            # Check additional_kwargs for tool responses
            if hasattr(message, 'additional_kwargs') and message.additional_kwargs:
                links = _extract_links_from_data(message.additional_kwargs)
                github_links.extend(links)
    
    # Remove duplicates while preserving order
    seen = set()
    unique_links = []
    for link in github_links:
        if link not in seen:
            seen.add(link)
            unique_links.append(link)
    
    return unique_links

def _extract_github_urls_from_text(text: str) -> List[str]:
    """Extract GitHub URLs from text content."""
    github_url_pattern = r'https://github\.com/[^\s\)\]\}\,\;]*'
    return re.findall(github_url_pattern, text)

def _extract_links_from_data(data: Any) -> List[str]:
    """Recursively extract GitHub links from nested data structures."""
    links = []
    
    if isinstance(data, dict):
        for key, value in data.items():
            if key in ['url', 'html_url', 'diff_url', 'patch_url', 'clone_url'] and isinstance(value, str):
                if 'github.com' in value:
                    links.append(value)
            else:
                links.extend(_extract_links_from_data(value))
    elif isinstance(data, list):
        for item in data:
            links.extend(_extract_links_from_data(item))
    elif isinstance(data, str):
        links.extend(_extract_github_urls_from_text(data))
    
    return links

def format_github_links_for_markdown(links: List[str], title: str = "Related GitHub Resources") -> str:
    """Format GitHub links as markdown list."""
    if not links:
        return ""
    
    markdown = f"\n### {title}\n\n"
    for link in links:
        # Try to extract repo name and create a meaningful link text
        link_text = _get_link_display_text(link)
        markdown += f"- [{link_text}]({link})\n"
    
    return markdown

def _get_link_display_text(url: str) -> str:
    """Extract meaningful display text from GitHub URL."""
    # Remove https://github.com/ prefix
    path = url.replace('https://github.com/', '')
    
    # Handle different URL types
    if '/issues/' in path:
        parts = path.split('/issues/')
        repo = parts[0]
        issue_num = parts[1].split('/')[0] if len(parts) > 1 else "unknown"
        return f"{repo} - Issue #{issue_num}"
    elif '/pull/' in path:
        parts = path.split('/pull/')
        repo = parts[0]
        pr_num = parts[1].split('/')[0] if len(parts) > 1 else "unknown"
        return f"{repo} - PR #{pr_num}"
    elif '/commit/' in path:
        parts = path.split('/commit/')
        repo = parts[0]
        commit = parts[1][:8] if len(parts) > 1 else "unknown"
        return f"{repo} - Commit {commit}"
    elif '/releases/' in path:
        parts = path.split('/releases/')
        repo = parts[0]
        return f"{repo} - Release"
    elif '/blob/' in path or '/tree/' in path:
        parts = path.split('/')
        if len(parts) >= 2:
            repo = f"{parts[0]}/{parts[1]}"
            return f"{repo} - File/Directory"
        return path
    else:
        # Default to repository name
        parts = path.split('/')
        if len(parts) >= 2:
            return f"{parts[0]}/{parts[1]}"
        return path

def extract_actionable_items_from_tool_response(tool_response: Dict[str, Any]) -> List[Dict[str, str]]:
    """Extract actionable items (issues, PRs, etc.) from GitHub tool responses."""
    actionable_items = []
    
    # Handle different types of GitHub API responses
    if isinstance(tool_response, dict):
        # Handle search results
        if 'items' in tool_response:
            for item in tool_response['items']:
                actionable_items.append(_format_actionable_item(item))
        # Handle direct list responses (like list_issues, list_pull_requests)
        elif isinstance(tool_response, list):
            for item in tool_response:
                actionable_items.append(_format_actionable_item(item))
        # Handle single item response
        else:
            actionable_items.append(_format_actionable_item(tool_response))
    elif isinstance(tool_response, list):
        for item in tool_response:
            actionable_items.append(_format_actionable_item(item))
    
    return actionable_items

def _format_actionable_item(item: Dict[str, Any]) -> Dict[str, str]:
    """Format a single GitHub item into actionable format."""
    formatted = {
        'title': item.get('title', 'Unknown'),
        'url': item.get('html_url', item.get('url', '')),
        'type': _determine_item_type(item),
        'description': item.get('body', '')[:200] + '...' if item.get('body') else '',
        'labels': ', '.join([label.get('name', '') for label in item.get('labels', [])]) if item.get('labels') else '',
        'state': item.get('state', 'unknown')
    }
    
    return formatted

def _determine_item_type(item: Dict[str, Any]) -> str:
    """Determine the type of GitHub item."""
    if 'pull_request' in item:
        return 'Pull Request'
    elif 'number' in item and 'title' in item:
        return 'Issue'
    elif 'name' in item and 'full_name' in item:
        return 'Repository'
    elif 'sha' in item:
        return 'Commit'
    else:
        return 'Unknown'