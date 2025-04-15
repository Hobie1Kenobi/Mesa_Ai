import json
import os
from collections import Counter
from typing import Dict, List
from datetime import datetime

def analyze_artist_data(file_path: str) -> Dict:
    """Analyze the artist data and return statistics."""
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    total_artists = data['total_artists']
    results = data['results']
    
    stats = {
        'total_artists': total_artists,
        'fields_coverage': {},
        'contact_info_stats': {
            'has_email': 0,
            'has_website': 0,
            'social_media_platforms': Counter(),
            'artists_with_social_media': 0
        },
        'release_stats': {
            'total_releases': 0,
            'artists_with_releases': 0,
            'releases_per_artist': [],
            'earliest_release': None,
            'latest_release': None
        },
        'country_distribution': Counter(),
        'artist_types': Counter(),
        'inconsistencies': {
            'by_type': Counter(),
            'by_severity': Counter()
        }
    }
    
    # Analyze basic fields coverage
    fields = ['id', 'name', 'type', 'country', 'disambiguation', 'releases', 'urls', 'relations']
    for field in fields:
        stats['fields_coverage'][field] = sum(1 for artist in results if artist.get(field) is not None)
    
    for artist in results:
        # Contact information
        contact_info = artist.get('contact_info', {})
        if contact_info.get('email'):
            stats['contact_info_stats']['has_email'] += 1
        if contact_info.get('website'):
            stats['contact_info_stats']['has_website'] += 1
        if contact_info.get('social_media'):
            stats['contact_info_stats']['artists_with_social_media'] += 1
            for social in contact_info['social_media']:
                stats['contact_info_stats']['social_media_platforms'][social['platform']] += 1
        
        # Releases
        releases = artist.get('releases', [])
        if releases:
            stats['release_stats']['artists_with_releases'] += 1
            stats['release_stats']['total_releases'] += len(releases)
            stats['release_stats']['releases_per_artist'].append(len(releases))
            
            # Track release dates
            dates = [release['date'] for release in releases if release.get('date')]
            if dates:
                try:
                    valid_dates = [datetime.strptime(date.split('-')[0], '%Y') for date in dates]
                    if valid_dates:
                        earliest = min(valid_dates)
                        latest = max(valid_dates)
                        if not stats['release_stats']['earliest_release'] or earliest < stats['release_stats']['earliest_release']:
                            stats['release_stats']['earliest_release'] = earliest
                        if not stats['release_stats']['latest_release'] or latest > stats['release_stats']['latest_release']:
                            stats['release_stats']['latest_release'] = latest
                except ValueError:
                    pass
        
        # Country and type distribution
        if artist.get('country'):
            stats['country_distribution'][artist['country']] += 1
        if artist.get('type'):
            stats['artist_types'][artist['type']] += 1
        
        # Inconsistencies
        for issue in artist.get('inconsistencies', []):
            stats['inconsistencies']['by_type'][issue['type']] += 1
            stats['inconsistencies']['by_severity'][issue['severity']] += 1
    
    # Calculate averages and percentages
    if stats['release_stats']['artists_with_releases'] > 0:
        stats['release_stats']['avg_releases_per_artist'] = (
            stats['release_stats']['total_releases'] / stats['release_stats']['artists_with_releases']
        )
    
    # Convert datetime objects to strings for JSON serialization
    if stats['release_stats']['earliest_release']:
        stats['release_stats']['earliest_release'] = stats['release_stats']['earliest_release'].year
    if stats['release_stats']['latest_release']:
        stats['release_stats']['latest_release'] = stats['release_stats']['latest_release'].year
    
    return stats

def main():
    # Find the most recent scan file
    output_dir = "output/hip_hop_analysis"
    files = [f for f in os.listdir(output_dir) if f.startswith('hip_hop_scan_')]
    if not files:
        print("No scan files found")
        return
    
    latest_file = max(files)
    file_path = os.path.join(output_dir, latest_file)
    
    # Analyze the data
    stats = analyze_artist_data(file_path)
    
    # Save the analysis results
    output_file = os.path.join(output_dir, f'analysis_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json')
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(stats, f, indent=2, ensure_ascii=False)
    
    print(f"Analysis saved to {output_file}")
    
    # Print summary
    print("\nSummary of available information:")
    print(f"Total artists analyzed: {stats['total_artists']}")
    print("\nField coverage (percentage of artists with data):")
    for field, count in stats['fields_coverage'].items():
        percentage = (count / stats['total_artists']) * 100
        print(f"- {field}: {percentage:.1f}%")
    
    print("\nContact information:")
    print(f"- Artists with email: {stats['contact_info_stats']['has_email']}")
    print(f"- Artists with website: {stats['contact_info_stats']['has_website']}")
    print(f"- Artists with social media: {stats['contact_info_stats']['artists_with_social_media']}")
    
    print("\nRelease information:")
    print(f"- Total releases: {stats['release_stats']['total_releases']}")
    print(f"- Artists with releases: {stats['release_stats']['artists_with_releases']}")
    if stats['release_stats']['artists_with_releases'] > 0:
        print(f"- Average releases per artist: {stats['release_stats']['avg_releases_per_artist']:.1f}")
    if stats['release_stats']['earliest_release'] and stats['release_stats']['latest_release']:
        print(f"- Release date range: {stats['release_stats']['earliest_release']} - {stats['release_stats']['latest_release']}")
    
    print("\nTop 5 countries:")
    for country, count in stats['country_distribution'].most_common(5):
        print(f"- {country}: {count}")
    
    print("\nArtist types:")
    for type_, count in stats['artist_types'].items():
        print(f"- {type_}: {count}")
    
    print("\nInconsistencies by severity:")
    for severity, count in stats['inconsistencies']['by_severity'].items():
        print(f"- {severity}: {count}")

if __name__ == "__main__":
    main() 