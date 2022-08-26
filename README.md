# class-model-dsl
DSL parser to support the SM Metamodel Class Model

There is an existing .xmm file format that captures a partial class model for the purposes of generating diagrams using the Flatland diagram generator.

But the existing .xmm format was stripped out of a larger DSL. Now that we have a good first draft of the Shlaer Mellor Metamodel on this site, it's time to start parsing!

So we will extend the .xmm format to handle a complete class model.

The initial goal of this parser will be to populate an sqlite3 database schema (also to be defined).

Once we get this done we can move on to the remainder of the metamodel (state and action semantics).

But, first things first!
