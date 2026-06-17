"""
Example: Using the LLM Provider System

Demonstrates how to use different LLM providers with the configuration system.
"""

from app.config.llm_config import (
    create_llm,
    track_usage,
    get_usage_stats,
    reset_usage_stats,
    get_llm_info,
    get_llm_config
)


def example_basic_usage():
    """Example 1: Basic LLM usage"""
    print("\n" + "="*60)
    print("Example 1: Basic LLM Usage")
    print("="*60)
    
    # Create LLM with default config from .env
    llm = create_llm()
    
    # Get LLM info
    info = get_llm_info()
    print(f"\nUsing Provider: {info['provider']}")
    print(f"Model: {info['model']}")
    print(f"Temperature: {info['temperature']}")
    
    # Make a request
    query = "What is the capital of France?"
    print(f"\nQuery: {query}")
    
    response = llm.invoke(query)
    print(f"Response: {response.content}")
    
    # Track usage and cost
    cost = track_usage(response)
    print(f"Cost: ${cost:.6f}")


def example_custom_config():
    """Example 2: Custom configuration"""
    print("\n" + "="*60)
    print("Example 2: Custom Configuration")
    print("="*60)
    
    # Create LLM with custom settings
    llm = create_llm(
        temperature=0.3,  # Lower temperature for more focused responses
        max_tokens=500    # Limit response length
    )
    
    query = "Explain quantum computing in one sentence."
    print(f"\nQuery: {query}")
    print("Settings: temperature=0.3, max_tokens=500")
    
    response = llm.invoke(query)
    print(f"Response: {response.content}")
    
    cost = track_usage(response)
    print(f"Cost: ${cost:.6f}")


def example_streaming():
    """Example 3: Streaming responses"""
    print("\n" + "="*60)
    print("Example 3: Streaming Responses")
    print("="*60)
    
    # Create LLM with streaming enabled
    llm = create_llm(streaming=True)
    
    query = "Write a short poem about AI."
    print(f"\nQuery: {query}")
    print("Response (streaming):")
    
    # Stream the response
    for chunk in llm.stream(query):
        print(chunk.content, end="", flush=True)
    
    print("\n")


def example_cost_tracking():
    """Example 4: Cost tracking"""
    print("\n" + "="*60)
    print("Example 4: Cost Tracking")
    print("="*60)
    
    # Reset stats
    reset_usage_stats()
    
    llm = create_llm()
    
    # Make multiple requests
    queries = [
        "What is machine learning?",
        "Explain neural networks.",
        "What is deep learning?"
    ]
    
    print("\nMaking 3 requests...")
    for i, query in enumerate(queries, 1):
        print(f"\n{i}. {query}")
        response = llm.invoke(query)
        cost = track_usage(response)
        print(f"   Response: {response.content[:100]}...")
        print(f"   Cost: ${cost:.6f}")
    
    # Get total statistics
    stats = get_usage_stats()
    print("\n" + "-"*60)
    print("Total Statistics:")
    print(f"  Provider: {stats['provider']}")
    print(f"  Model: {stats['model']}")
    print(f"  Total Input Tokens: {stats['total_input_tokens']:,}")
    print(f"  Total Output Tokens: {stats['total_output_tokens']:,}")
    print(f"  Total Tokens: {stats['total_tokens']:,}")
    print(f"  Total Cost: ${stats['total_cost_usd']:.4f}")
    print(f"  Avg Cost/1K tokens: ${stats['average_cost_per_request']:.6f}")


def example_provider_comparison():
    """Example 5: Compare different providers"""
    print("\n" + "="*60)
    print("Example 5: Provider Comparison")
    print("="*60)
    
    import os
    
    query = "Explain AI in one sentence."
    
    # Save original provider
    original_provider = os.getenv("LLM_PROVIDER", "ollama")
    
    providers = ["ollama", "openai", "anthropic"]
    
    for provider in providers:
        print(f"\n{'-'*60}")
        print(f"Testing Provider: {provider.upper()}")
        print('-'*60)
        
        # Set provider
        os.environ["LLM_PROVIDER"] = provider
        
        try:
            # Create new config
            from app.config import llm_config
            llm_config._llm_config = None  # Reset global config
            
            llm = create_llm()
            info = get_llm_info()
            
            print(f"Model: {info['model']}")
            print(f"Query: {query}")
            
            response = llm.invoke(query)
            print(f"Response: {response.content}")
            
            cost = track_usage(response)
            print(f"Cost: ${cost:.6f}")
            
        except Exception as e:
            print(f"Error: {e}")
            print(f"(Make sure {provider.upper()} is configured in .env)")
    
    # Restore original provider
    os.environ["LLM_PROVIDER"] = original_provider


def example_error_handling():
    """Example 6: Error handling and fallback"""
    print("\n" + "="*60)
    print("Example 6: Error Handling")
    print("="*60)
    
    import os
    
    # Try to use a provider that might not be configured
    os.environ["LLM_PROVIDER"] = "openai"
    
    try:
        llm = create_llm()
        response = llm.invoke("Hello!")
        print(f"Success with OpenAI: {response.content}")
    except Exception as e:
        print(f"OpenAI failed: {e}")
        print("Falling back to Ollama...")
        
        # Fallback to Ollama
        os.environ["LLM_PROVIDER"] = "ollama"
        from app.config import llm_config
        llm_config._llm_config = None  # Reset config
        
        llm = create_llm()
        response = llm.invoke("Hello!")
        print(f"Success with Ollama: {response.content}")


def example_batch_processing():
    """Example 7: Batch processing with cost tracking"""
    print("\n" + "="*60)
    print("Example 7: Batch Processing")
    print("="*60)
    
    reset_usage_stats()
    
    llm = create_llm()
    
    # Simulate processing multiple emails
    emails = [
        "Meeting scheduled for tomorrow at 10 AM",
        "Please review the attached document",
        "Urgent: Server maintenance tonight",
        "Thank you for your feedback",
        "Project deadline extended to next week"
    ]
    
    print(f"\nProcessing {len(emails)} emails...")
    
    summaries = []
    for i, email in enumerate(emails, 1):
        query = f"Summarize this email in 5 words: {email}"
        response = llm.invoke(query)
        summary = response.content
        summaries.append(summary)
        
        cost = track_usage(response)
        print(f"{i}. {summary} (${cost:.6f})")
    
    # Show total cost
    stats = get_usage_stats()
    print(f"\nTotal cost for {len(emails)} emails: ${stats['total_cost_usd']:.4f}")
    print(f"Average cost per email: ${stats['total_cost_usd']/len(emails):.6f}")


def main():
    """Run all examples"""
    print("\n" + "="*80)
    print("LLM PROVIDER SYSTEM - USAGE EXAMPLES")
    print("="*80)
    
    examples = [
        ("Basic Usage", example_basic_usage),
        ("Custom Configuration", example_custom_config),
        ("Streaming", example_streaming),
        ("Cost Tracking", example_cost_tracking),
        ("Provider Comparison", example_provider_comparison),
        ("Error Handling", example_error_handling),
        ("Batch Processing", example_batch_processing)
    ]
    
    print("\nAvailable Examples:")
    for i, (name, _) in enumerate(examples, 1):
        print(f"  {i}. {name}")
    
    print("\nRunning all examples...")
    print("(Note: Some examples may fail if providers are not configured)")
    
    for name, example_func in examples:
        try:
            example_func()
        except Exception as e:
            print(f"\n✗ Example '{name}' failed: {e}")
    
    print("\n" + "="*80)
    print("EXAMPLES COMPLETE")
    print("="*80)
    print("\nTo run specific example:")
    print("  python example_llm_usage.py")
    print("\nTo configure providers:")
    print("  1. Copy .env.example to .env")
    print("  2. Add your API keys")
    print("  3. Set LLM_PROVIDER")
    print("\nSee LLM_PROVIDER_GUIDE.md for detailed instructions.")


if __name__ == "__main__":
    main()

# Made with Bob
