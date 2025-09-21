# /deep-researcher-agent/quick_formula_fix.py
"""
Quick fix to help your agent find formulas by using more targeted search terms
"""

def create_formula_search_tool(query_engine):
    """Create a search tool that specifically looks for formulas"""
    
    def enhanced_formula_search(input: str) -> str:
        """Search with formula-specific terms"""
        original_query = input
        
        # If looking for formulas, try multiple specific searches
        if any(word in input.lower() for word in ['formula', 'equation', 'mathematical']):
            
            searches_to_try = [
                original_query,
                original_query.replace('formula', 'equation'),
                original_query + ' mathematical expression',
                original_query + ' cross-attention mechanism',
                original_query + ' multi-head attention',
                # For Memory Attn-Adapter specifically
                'Memory Attn-Adapter cross-attention mechanism equation',
                'MLPK MLPQ attention formula',
                'ˆF = F⊤σ',
                'ŵ = w + p(w)',
                # Look for equation numbers
                'equation (4)',
                'equation (5)',
                # Look for specific symbols
                '⊤ σ MLP',
                'Hadamard product ⊙',
            ]
            
            results = []
            for search_term in searches_to_try:
                try:
                    response = query_engine.query(search_term)
                    result = str(response)
                    if result and len(result) > 50 and 'no' not in result.lower()[:50]:
                        results.append(f"Search '{search_term}': {result}")
                        if any(symbol in result for symbol in ['=', '⊤', 'σ', '√', '⊙']):
                            # Found mathematical symbols, this is likely good
                            break
                except:
                    continue
            
            if results:
                return "FORMULA SEARCH RESULTS:\n" + "\n\n".join(results[:3])
            else:
                return f"Could not find mathematical formulas for {original_query}. The documents may contain the concept but not explicit equations."
        
        # Regular search for non-formula queries
        else:
            response = query_engine.query(original_query)
            return str(response)
    
    return enhanced_formula_search

# Update your agent.py to use this:
def setup_enhanced_agent():
    """Setup agent with formula-aware search"""
    from retrieval import setup_query_engine, rate_limiter
    from llama_index.core.tools import FunctionTool
    from llama_index.core.agent import ReActAgent
    from llama_index.core import Settings
    
    query_engine = setup_query_engine()
    enhanced_search = create_formula_search_tool(query_engine)
    
    def rate_limited_enhanced_search(input: str) -> str:
        try:
            rate_limiter.wait_if_needed("gemini")
            return enhanced_search(input)
        except Exception as e:
            return f"Search error: {e}"
    
    search_tool = FunctionTool.from_defaults(
        fn=rate_limited_enhanced_search,
        name="local_document_retriever",
        description=(
            "Search documents with enhanced formula detection. "
            "Automatically tries multiple search strategies for mathematical content."
        )
    )
    
    system_prompt = """
    You are a research assistant with enhanced formula search capabilities.
    
    IMPORTANT: For questions about formulas:
    1. First search for the concept name
    2. Then search adding "formula" or "equation" 
    3. Look for mathematical symbols in results (=, ⊤, σ, √, ⊙)
    4. Try searching for specific equation numbers if mentioned
    
    Make multiple targeted searches before concluding no formula exists.
    """
    
    agent = ReActAgent.from_tools(
        tools=[search_tool],
        llm=Settings.llm,
        system_prompt=system_prompt,
        max_iterations=10,
        verbose=True
    )
    
    return agent

if __name__ == "__main__":
    # Quick test
    agent = setup_enhanced_agent()
    response = agent.chat("Can you provide the formula for Memory Attn-Adapter?")
    print(response)