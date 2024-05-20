const { Client, ActivityType, GatewayIntentBits, ChannelType, PermissionsBitField, ActionRowBuilder, ButtonBuilder, ButtonStyle, StringSelectMenuBuilder, ComponentType, EmbedBuilder } = require('discord.js');
const config = require('./config.json');

const client = new Client({
    intents: [
        GatewayIntentBits.Guilds,
        GatewayIntentBits.GuildMessages,
        GatewayIntentBits.MessageContent,
        GatewayIntentBits.DirectMessages
    ],
    partials: ['CHANNEL'] 
});

client.on('ready', () => {
    console.log(`Logged in as ${client.user.tag}!`);

    client.user.setActivity({
        name: 'Delta Tickets',
        type: ActivityType.Watching,
        status: 'dnd'
});
});


client.on('messageCreate', async message => {
    if (!message.content.startsWith(config.prefix) || message.author.bot) return;

    const args = message.content.slice(config.prefix.length).trim().split(/ +/);
    const command = args.shift().toLowerCase();

    if (command === 'setupticket') {
        const embed = new EmbedBuilder()
            .setColor('#ffffff')
            .setTitle('Ticket | Delta')
            .setDescription('Please click the button below to open a new ticket.');

        await message.reply({
            embeds: [embed],
            components: [
                new ActionRowBuilder().addComponents(
                    new ButtonBuilder()
                        .setCustomId('ticket-open')
                        .setLabel('Open Ticket')
                        .setStyle(ButtonStyle.Primary)
                )
            ]
        });

        const collector = message.channel.createMessageComponentCollector({
            componentType: ComponentType.Button,
        });

        collector.on('collect', async interaction => {
            if (interaction.customId === 'ticket-open') {
                try {
                    await interaction.user.send({
                        content: `Server ID: ${interaction.guild.id}\nPlease select a reason for your ticket:`,
                        components: [
                            new ActionRowBuilder().addComponents(
                                new StringSelectMenuBuilder()
                                    .setCustomId('ticket-reason')
                                    .setPlaceholder('Select a reason')
                                    .addOptions([
                                        {
                                            label: 'Bug report',
                                            value: 'bug'
                                        },
                                        {
                                            label: 'Support about the bot',
                                            value: 'support'
                                        },
                                        {
                                            label: 'Other',
                                            value: 'other'
                                        }
                                    ])
                                    .setMaxValues(1)
                                    .setMinValues(1)
                            )
                        ]
                    });

                    await interaction.reply({ content: 'Check your DMs to complete the ticket setup.', ephemeral: true });
                } catch (error) {
                    await interaction.reply({ content: 'I cannot send you a DM. Please check your DM settings.', ephemeral: true });
                }
            }
        });
    }
});

client.on('interactionCreate', async interaction => {
    if (!interaction.isStringSelectMenu()) return;

    if (interaction.customId === 'ticket-reason') {
        const reason = interaction.values[0];
        const guild = client.guilds.cache.get(interaction.message.content.split('Server ID: ')[1].split('\n')[0]);

        if (!guild) {
            await interaction.reply({
                content: 'Error: Could not find the guild.',
                ephemeral: true
            });
            return;
        }

        const ticketCategory = guild.channels.cache.find(c => c.name === 'tickets');
        const ticketChannelName = `ticket-${interaction.user.id}`;
        const ticketChannelExists = guild.channels.cache.find(c => c.name === ticketChannelName);

        if (ticketChannelExists) {
            await interaction.reply({
                content: 'You already have an open ticket. Please use that instead.',
                ephemeral: true
            });
            return;
        }

        const newTicketChannel = await guild.channels.create({
            name: ticketChannelName,
            type: ChannelType.GuildText,
            parent: ticketCategory ? ticketCategory.id : null,
            permissionOverwrites: [
                {
                    id: guild.roles.everyone,
                    deny: [PermissionsBitField.Flags.ViewChannel]
                },
                {
                    id: interaction.user.id,
                    allow: [PermissionsBitField.Flags.ViewChannel, PermissionsBitField.Flags.SendMessages, PermissionsBitField.Flags.ReadMessageHistory]
                }
            ]
        });

        await newTicketChannel.send({
            embeds: [
                new EmbedBuilder()
                    .setColor('#ffffff')
                    .setTitle(`Hello ${interaction.user.username}, your ticket has been created.`)
                    .setDescription('Please describe your issue below.')
            ],
            components: [
                new ActionRowBuilder().addComponents(
                    new ButtonBuilder()
                        .setCustomId('close-ticket')
                        .setLabel('Close Ticket')
                        .setStyle(ButtonStyle.Danger),
                    new ButtonBuilder()
                        .setCustomId('claim-ticket')
                        .setLabel('Claim Ticket')
                        .setStyle(ButtonStyle.Secondary)
                )
            ]
        });
        await interaction.reply({
            content: `Your ticket has been created in ${newTicketChannel}. Reason: ${reason}`,
            ephemeral: true
        });

        const ticketCollector = newTicketChannel.createMessageComponentCollector({
            componentType: ComponentType.Button,
        });

        ticketCollector.on('collect', async ticketInteraction => {
            if (ticketInteraction.customId === 'close-ticket') {
                await newTicketChannel.delete();
                await ticketInteraction.reply({
                    content: 'The ticket has been closed.',
                    ephemeral: true
                });
            } else if (ticketInteraction.customId === 'claim-ticket') {
                if (ticketInteraction.member.permissions.has(PermissionsBitField.Flags.Administrator)) {
                    await ticketInteraction.reply({
                        content: `This ticket has been claimed by ${ticketInteraction.user.username}.`,
                        ephemeral: false
                    });
                } else {
                    await ticketInteraction.reply({
                        content: 'You do not have permission to claim this ticket.',
                        ephemeral: true
                    });
                }
            }
        });
    }
});

client.login(config.token);
