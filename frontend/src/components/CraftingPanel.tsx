import React, { useState } from 'react';
import { useWorldStateQuery } from '../api';
import './CraftingPanel.css';

export const CraftingPanel: React.FC = () => {
    const { data: worldData } = useWorldStateQuery(1); // Assuming character ID 1 for now
    const [selectedRecipe, setSelectedRecipe] = useState<string | null>(null);

    if (!worldData || !worldData.state.player_stats) {
        return <div>Loading crafting data...</div>;
    }

    const { known_recipes, crafting_proficiencies } = worldData.state.player_stats;

    // Hardcoded recipe DB for demonstration
    const recipesDb: Record<string, any> = {
        'copper_wire': { name: 'Copper Wire', branch: 'Metallurgy', materials: '2x Copper Ore', tier: 1 },
        'basic_potion': { name: 'Basic Potion', branch: 'Alchemy', materials: '1x Herb, 1x Water', tier: 1 },
        'gearbox': { name: 'Gearbox', branch: 'Clockwork', materials: '3x Brass, 1x Spring', tier: 2 },
    };

    const handleCraft = async () => {
        if (!selectedRecipe) return;
        const recipeInfo = recipesDb[selectedRecipe];
        if (!recipeInfo) return;

        try {
            const response = await fetch('/gameplay/craft', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    character_id: 1,
                    recipe_id: selectedRecipe,
                    branch: recipeInfo.branch
                })
            });
            const result = await response.json();
            alert(`${result.message} (Prob: ${(result.probability * 100).toFixed(0)}%)`);
        } catch (e) {
            console.error(e);
        }
    };

    return (
        <div className="crafting-panel glass-panel">
            <h2>Crafting Workbench</h2>
            <div className="proficiencies">
                <h3>Proficiencies</h3>
                <ul>
                    {Object.entries(crafting_proficiencies || {}).map(([branch, level]) => (
                        <li key={branch}>{branch}: Lvl {level as number}</li>
                    ))}
                </ul>
            </div>
            <div className="recipes-list">
                <h3>Known Recipes</h3>
                {known_recipes && known_recipes.length > 0 ? (
                    <ul>
                        {known_recipes.map((recipeId: string) => {
                            const info = recipesDb[recipeId] || { name: recipeId, branch: 'Unknown' };
                            return (
                                <li 
                                    key={recipeId} 
                                    onClick={() => setSelectedRecipe(recipeId)}
                                    className={selectedRecipe === recipeId ? 'selected' : ''}
                                >
                                    {info.name}
                                </li>
                            );
                        })}
                    </ul>
                ) : (
                    <p>No recipes known.</p>
                )}
            </div>
            
            {selectedRecipe && recipesDb[selectedRecipe] && (
                <div className="recipe-details">
                    <h3>{recipesDb[selectedRecipe].name} Details</h3>
                    <p><strong>Branch:</strong> {recipesDb[selectedRecipe].branch}</p>
                    <p><strong>Materials:</strong> {recipesDb[selectedRecipe].materials}</p>
                    <p><strong>Required Facility Tier:</strong> {recipesDb[selectedRecipe].tier}</p>
                    
                    <button onClick={handleCraft} className="primary-btn">Attempt Craft</button>
                </div>
            )}
        </div>
    );
};
