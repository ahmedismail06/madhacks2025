import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend (essential for Flask/Servers)
import matplotlib.pyplot as plt
import io

def generate_path_svg(path_data):
    """
    Generates an SVG plot of the path in memory.
    
    Args:
        path_data (list): List of dicts [{'x': 1, 'y': 2, 'type': '...'}, ...]
    
    Returns:
        str: The raw SVG XML string.
    """
    if not path_data:
        return None

    # 1. Extract coordinates
    xs = [p['x'] for p in path_data]
    ys = [p['y'] for p in path_data]

    # 2. Create Figure and Axis
    # figsize is in inches, but SVG scales. 5x5 is a good aspect ratio.
    fig, ax = plt.subplots(figsize=(5, 5))

    # 3. Plot the Path
    # '-o' means connect points with lines (-) and show dots (o)
    ax.plot(xs, ys, '-o', color='#3b82f6', linewidth=2, markersize=4, label='Path')

    # 4. Highlight Start and End
    ax.plot(xs[0], ys[0], 'go', markersize=8, label='Start') # Green Start
    ax.plot(xs[-1], ys[-1], 'ro', markersize=8, label='End') # Red End

    # 5. Styling
    ax.set_title("Calculated Route")
    ax.grid(True, linestyle='--', alpha=0.6)
    
    # OPTIONAL: Invert Y-axis? 
    # In many grid systems (like arrays), (0,0) is top-left. 
    # Matplotlib is bottom-left by default. Uncomment below if your map looks upside down.
    # ax.invert_yaxis() 

    # Ensure integer ticks for grid clarity
    ax.xaxis.get_major_locator().set_params(integer=True)
    ax.yaxis.get_major_locator().set_params(integer=True)

    # 6. Save to Memory Buffer (RAM)
    img_buffer = io.BytesIO()
    
    # 'bbox_inches="tight"' removes extra white whitespace around the plot
    plt.savefig(img_buffer, format='svg', bbox_inches='tight')
    
    # Close plot to free memory (Critical in web servers!)
    plt.close(fig)
    
    # 7. Retrieve data
    img_buffer.seek(0)
    svg_data = img_buffer.read().decode('utf-8')
    
    return svg_data