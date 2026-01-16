"""
SYSMIND Startup Manager Module

Manage system startup programs.
"""

from typing import List, Dict, Optional, Any
from dataclasses import dataclass

from ...utils.platform_utils import get_adapter, is_admin
from ...core.errors import PermissionError, ProcessError


@dataclass
class StartupItem:
    """Startup program information."""
    name: str
    command: str
    location: str
    type: str  # registry, startup_folder, launchagent, desktop_file
    enabled: bool


class StartupManager:
    """
    Manage system startup programs.
    
    Cross-platform support for viewing and modifying
    programs that run at system startup.
    """
    
    def __init__(self):
        self.platform = get_adapter()
        self._cache: Optional[List[StartupItem]] = None
    
    def list_startup_items(self, refresh: bool = False) -> List[StartupItem]:
        """
        List all startup programs.
        
        Args:
            refresh: Force refresh of cached data
        
        Returns:
            List of StartupItem
        """
        if self._cache is not None and not refresh:
            return self._cache
        
        items = []
        raw_items = self.platform.get_startup_items()
        
        for item in raw_items:
            items.append(StartupItem(
                name=item['name'],
                command=item.get('command', ''),
                location=item.get('location', ''),
                type=item.get('type', 'unknown'),
                enabled=item.get('enabled', True)
            ))
        
        self._cache = items
        return items
    
    def disable_startup_item(self, name: str) -> bool:
        """
        Disable a startup program.
        
        Args:
            name: Name of the startup item
        
        Returns:
            True if successful
        
        Raises:
            PermissionError: If elevated privileges are required
        """
        # Find the item
        items = self.list_startup_items(refresh=True)
        item = next((i for i in items if i.name == name), None)
        
        if not item:
            raise ProcessError(f"Startup item not found: {name}")
        
        # Try to disable
        success = self.platform.disable_startup_item(name)
        
        if success:
            # Update cache
            self._cache = None
        
        return success
    
    def enable_startup_item(self, name: str) -> bool:
        """
        Enable a startup program.
        
        Args:
            name: Name of the startup item
        
        Returns:
            True if successful
        """
        success = self.platform.enable_startup_item(name)
        
        if success:
            self._cache = None
        
        return success
    
    def analyze_startup_impact(self) -> Dict[str, Any]:
        """
        Analyze potential impact of startup programs.
        
        Returns:
            Dictionary with analysis results
        """
        items = self.list_startup_items(refresh=True)
        
        # Categorize by type
        by_type: Dict[str, int] = {}
        for item in items:
            by_type[item.type] = by_type.get(item.type, 0) + 1
        
        # Known heavy programs (simplified)
        heavy_programs = [
            'steam', 'discord', 'spotify', 'skype', 
            'slack', 'teams', 'zoom', 'dropbox', 
            'onedrive', 'google', 'adobe', 'creative cloud'
        ]
        
        potentially_heavy = []
        for item in items:
            name_lower = item.name.lower()
            if any(h in name_lower for h in heavy_programs):
                potentially_heavy.append(item.name)
        
        return {
            'total_items': len(items),
            'by_type': by_type,
            'potentially_heavy': potentially_heavy,
            'enabled_count': sum(1 for i in items if i.enabled),
            'recommendation': 'Consider disabling heavy programs' if len(potentially_heavy) > 3 else 'Startup looks reasonable'
        }
    
    def get_recommendations(self) -> List[Dict[str, Any]]:
        """
        Get recommendations for startup optimization.
        
        Returns:
            List of recommendation dictionaries
        """
        items = self.list_startup_items(refresh=True)
        recommendations = []
        
        # Categories of programs
        categories = {
            'updaters': ['update', 'updater', 'autoupdate'],
            'sync': ['sync', 'cloud', 'drive', 'dropbox', 'onedrive'],
            'chat': ['discord', 'slack', 'teams', 'skype', 'zoom'],
            'media': ['spotify', 'itunes', 'steam'],
            'security': ['antivirus', 'defender', 'security', 'norton', 'mcafee'],
        }
        
        for item in items:
            name_lower = item.name.lower()
            
            # Check for updaters (usually safe to disable)
            for cat, keywords in categories.items():
                if any(k in name_lower for k in keywords):
                    if cat == 'updaters':
                        recommendations.append({
                            'item': item.name,
                            'category': cat,
                            'suggestion': 'Can usually be disabled safely',
                            'priority': 'low',
                            'impact': 'Faster startup, may miss updates'
                        })
                    elif cat == 'sync':
                        recommendations.append({
                            'item': item.name,
                            'category': cat,
                            'suggestion': 'Disable if not frequently used',
                            'priority': 'medium',
                            'impact': 'Faster startup, delayed sync'
                        })
                    elif cat == 'chat':
                        recommendations.append({
                            'item': item.name,
                            'category': cat,
                            'suggestion': 'Disable if not needed immediately on boot',
                            'priority': 'medium',
                            'impact': 'Faster startup, manual launch needed'
                        })
                    elif cat == 'security':
                        recommendations.append({
                            'item': item.name,
                            'category': cat,
                            'suggestion': 'Keep enabled for protection',
                            'priority': 'high',
                            'impact': 'Required for security'
                        })
                    break
        
        return recommendations
    
    def export_startup_list(self) -> str:
        """
        Export startup items to a formatted string.
        
        Returns:
            Formatted string of startup items
        """
        items = self.list_startup_items(refresh=True)
        
        lines = ["Startup Programs Report", "=" * 50, ""]
        
        for item in sorted(items, key=lambda x: x.name.lower()):
            status = "Enabled" if item.enabled else "Disabled"
            lines.append(f"Name: {item.name}")
            lines.append(f"  Command: {item.command}")
            lines.append(f"  Location: {item.location}")
            lines.append(f"  Type: {item.type}")
            lines.append(f"  Status: {status}")
            lines.append("")
        
        return "\n".join(lines)
