# Decentralized Control Synthesis for Air Traffic Management in UAM

## Suda Bharadwaj, Steven Carr, Natasha Neogi, Ufuk Topcu

Visualization tools for showing urban air mobility (UAM) traffic management problems. 


### Examples on simulated airpsaces

In these simulations the <strong>vehicles</strong> are indicated by the following colors:
<ul>
<li>Red - Landing vehicle, </li>
<li>Yellow - Allocated (assigned a landing or pass-through) vehicle, </li>
<li>Orange - Loitering vehicle awaiting allocation,</li>
<li>Green - Moving unallocated vehicle.</li>
</ul>

Furthermore the region inside of a <strong>vertihub</strong> is indicated by a colored ring, the colors have the following meanings
<ul>
<li>Blue - Not a scheduling vertihub (uncontrolled regions),</li>
<li>Green - Three unallocated slots,</li>
<li>Yellow - Two unallocated slots, </li>
<li>Orange - One unallocated slots,</li>
<li>Red - No free slots (vertihub cannot control any more vehicles).</li>
</ul>


##### <em> Sparsely interacting vertihubs </em>

With sparsely interacting vertihubs, the vehicles tend to loiter around the edges of a vertihub as they attempt to either land or pass-through.

{% include youtube_sparse.html %}

#####  <em> Closely interacting vertihubs </em>

With closely interacting vertihubs, the vehicles tend to loiter around the top vertihub as it waits to clear additional vehicles to open slots. Additionally as vehicles leave a region they often need to loiter as they do not have permission to move through the new vertihub.

{% include youtube_interacting.html %}

##### <em> Fully connected vertihubs </em>

When the vertihubs are fully connected, the vehicles tend to loiter as they take-off, waiting for permissions to move. When permission is granted, the vehicles rarely loiter until they land.

{% include youtube_all.html %}
